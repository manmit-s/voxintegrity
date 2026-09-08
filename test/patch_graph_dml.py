"""Rewrite ast_finetuned_fp32.onnx so every Reshape has a constant shape tensor.

DirectML's Reshape implementation cannot execute this graph when the shape tensor is
computed at runtime (Concat of Shape(input_values) slices and int64 constants). The
backend always feeds batch=1, so we specialize batch_size=1, run ONNX shape inference,
and replace each Reshape's dynamic shape input with a constant initializer.

Output: ml_pipeline/weights/ast_finetuned_fp32_dml.onnx (shares the same .onnx.data).
"""

import sys
from pathlib import Path

import numpy as np
import onnx
from onnx import TensorProto, helper, numpy_helper

SRC = Path('ml_pipeline/weights/ast_finetuned_fp32.onnx')
DST = Path('ml_pipeline/weights/ast_finetuned_fp32_dml.onnx')
BATCH = 1

model = onnx.load(str(SRC), load_external_data=False)
g = model.graph

# 1. Specialize the dynamic batch dimension to 1 so shape inference can resolve everything.
for vi in list(g.input) + list(g.output) + list(g.value_info):
    if vi.type.tensor_type.HasField('shape'):
        for d in vi.type.tensor_type.shape.dim:
            if d.dim_param == 'batch_size':
                d.dim_param = ''
                d.dim_value = BATCH

# 2. Propagate concrete shapes through the whole graph.
inferred = onnx.shape_inference.infer_shapes(model, strict_mode=False, data_prop=True)
shapes: dict[str, list[int]] = {}
for vi in list(inferred.graph.value_info) + list(inferred.graph.input) + list(inferred.graph.output):
    if vi.type.tensor_type.HasField('shape') and vi.type.tensor_type.shape.dim:
        dims = [d.dim_value if d.HasField('dim_value') else -1 for d in vi.type.tensor_type.shape.dim]
        if all(d > 0 for d in dims):
            shapes[vi.name] = dims

g = inferred.graph
inits = {i.name for i in g.initializer}
producer = {out: n for n in g.node for out in n.output}

# 3. Rewrite every non-constant Reshape shape input with a constant initializer.
new_initializers: list[onnx.TensorProto] = []
rewired = 0
unresolved: list[str] = []
for n in g.node:
    if n.op_type != 'Reshape' or n.input[1] in inits:
        continue
    data_name = n.input[0]
    data_shape = shapes.get(data_name)
    if data_shape is None:
        unresolved.append(n.name)
        continue
    data_dims = len(data_shape)
    allow_zero = any(a.name == 'allowzero' for a in n.attribute)
    out_shape = shapes.get(n.output[0])
    if out_shape is None:
        unresolved.append(n.name)
        continue
    # Build a shape vector that reconstructs the same view: use the inferred output
    # shape directly, with 0 placeholders forbidden (DML) and -1 only where product
    # inference is required (matching the original reshape semantics).
    vec = np.array(out_shape, dtype=np.int64)
    init_name = f'{n.name}_shape_const'
    new_initializers.append(numpy_helper.from_array(vec, init_name))
    n.input[1] = init_name
    rewired += 1

if unresolved:
    print('UNRESOLVED Reshape nodes (left dynamic):', unresolved)

g.initializer.extend(new_initializers)
print(f'Rewired {rewired} Reshape nodes to constant shapes.')

# 4. Prune nodes made dead by the rewrite (Shape/Concat chains feeding only old reshapes).
changed = True
while changed:
    changed = False
    used: set[str] = set()
    for n in g.node:
        for inp in n.input:
            if inp:
                used.add(inp)
    for out in g.output:
        used.add(out.name)
    keep = []
    for n in list(g.node):
        if n.op_type in {'Shape', 'Concat', 'Unsqueeze', 'Slice', 'Gather', 'Cast', 'Expand'} \
                and all(o not in used for o in n.output):
            g.node.remove(n)
            changed = True
        else:
            keep.append(n)
    # Drop initializers that are no longer referenced.
    still_used: set[str] = set()
    for n in g.node:
        still_used.update(i for i in n.input if i)
    for out in g.output:
        still_used.add(out.name)
    for i in list(g.initializer):
        if i.name not in still_used and i.name not in {n.name for n in g.node}:
            if not (i.external_data or []):
                g.initializer.remove(i)

onnx.save(inferred, str(DST))
size = DST.stat().st_size
print(f'Saved {DST} ({size} bytes). Reshapes still dynamic:',
      sum(1 for n in inferred.graph.node if n.op_type == 'Reshape' and n.input[1] not in
          {i.name for i in inferred.graph.initializer}))
