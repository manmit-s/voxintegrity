import sys
from pathlib import Path

import onnx
from onnx import numpy_helper

path = Path('ml_pipeline/weights/ast_finetuned_fp32.onnx')
model = onnx.load(str(path))
g = model.graph
inits = {i.name for i in g.initializer}
producer = {out: n for n in g.node for out in n.output}

ops = set()
def collect(name, seen):
    if name in inits or name in seen:
        return
    n = producer.get(name)
    if n is None:
        return
    seen.add(name)
    ops.add(n.op_type)
    for inp in n.input:
        if inp:
            collect(inp, seen)

count = 0
for n in g.node:
    if n.op_type == 'Reshape' and n.input[1] not in inits:
        count += 1
        collect(n.input[1], set())
print('Reshapes with non-constant shape:', count)
print('Ops in their shape-computation DAGs:', sorted(ops))
# show input signature of graph input and dynamic axes
for i in g.input:
    dims = [(d.dim_param or d.dim_value) for d in i.type.tensor_type.shape.dim]
    print('graph input:', i.name, dims)
# attributes used by Shape nodes feeding reshapes
for n in g.node:
    if n.op_type == 'Shape' and n.output[0] in producer and any(True for _ in n.attribute):
        print('Shape with attrs:', n.name, [(a.name, [i for i in a.ints] or a.i) for a in n.attribute])

