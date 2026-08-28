# Git Sanity: SIH-2026 Team Workflow

> **Team:** Manmit, Soham, Vedant, Ninad, Devyani, Tanvi  
> **Goal:** Ek simple, safe aur PR-based Git workflow jisme **forks ki zarurat nahi hai**.

---

## 1. Sabse pehle: Hum kya use karenge?

Hamare paas **ek single private GitHub repository** hogi.

Usi repository mein sab teammates **collaborators** ke roop mein kaam karenge.

```text
                    PRIVATE GITHUB REPO
                           │
                           │
                     protected main
                           │
          ┌────────────────┼────────────────┐
          ↓                ↓                ↓
   feature/frontend   feature/ml      feature/backend
          │                │                │
          └──────────── Pull Requests ─────┘
                           │
                           ↓
                         main
```

### Important:

- ❌ 6 forks ki zarurat nahi
- ❌ Direct `main` push nahi
- ❌ Kisi ka feature branch mein doosre ka kaam unnecessarily edit nahi karna
- ✅ Har person apni feature branch par kaam karega
- ✅ Har completed feature ke liye PR banega
- ✅ PR review/merge Manmit karega
- ✅ `main` hamesha stable/working rakhne ki koshish karenge

---

# 2. Fork ki zarurat kyun nahi?

Fork mainly tab useful hota hai jab external/untrusted contributors ko repository mein directly access nahi dena ho.

Hum 6 log ek hi team hain aur sabko private repository ka collaborator access diya ja sakta hai.

Isliye simpler model:

```text
ONE REPO
   ↓
SIX COLLABORATORS
   ↓
EVERYONE HAS THEIR OWN BRANCH
   ↓
PR → main
```

Fork karne se yahan bas extra layer add hogi:

```text
Your repo
   ↓
Teammate fork
   ↓
Teammate branch
   ↓
PR back to your repo
```

Hackathon mein humein Git administration ka side quest nahi chahiye. Simple rakho.

---

# 3. `main` branch ka kya role hai?

`main` hamari **stable branch** hai.

Isko ideally aise treat karna hai:

> "Agar koi naya teammate ya judge repository clone kare, toh `main` par project ka reasonably working version hona chahiye."

Isliye:

```text
main = stable/integrated code
feature/* = individual development
```

### `main` par direct push nahi

Suppose kisi ne accidentally:

```bash
git push origin main
```

kar diya.

Hum ye avoid karna chahte hain.

GitHub par `main` ko **protected branch** bana denge.

Recommended rules:

- Require Pull Request before merging
- Require approval
- Disable direct pushes
- Disable force pushes
- Ideally require checks/tests to pass

Exact GitHub UI wording plan ke hisaab se change ho sakti hai, but principle same hai:

> **Main mein change = PR ke through.**

---

# 4. Har teammate ka branch

Suppose team members:

- Manmit
- Soham
- Vedant
- Ninad
- Devyani
- Tanvi

Apne respective work ke according branches bana sakte hain.

Example:

```text
main

feature/frontend
feature/backend-api
feature/classification
feature/segmentation
feature/preprocessing
feature/simulation
```

Branch naming consistent rakho.

Recommended:

```text
feature/<short-description>
```

Examples:

```text
feature/frontend-upload
feature/segmentation
feature/classification
feature/preprocessing
feature/backend-api
feature/simulation
```

---

# 5. Kaam start karne ka correct process

Sabse pehle repository clone karo:

```bash
git clone <PRIVATE_REPO_URL>
cd SIH-2026
```

Check:

```bash
git status
```

Latest `main` ensure karo:

```bash
git checkout main
git pull origin main
```

Ab apni branch banao:

```bash
git checkout -b feature/segmentation
```

Ab tumhari branch `main` ke current version se start hui.

---

# 6. Development ke time kya karna hai?

Apni branch par hi kaam karo.

Example:

```text
feature/segmentation
        ↓
model.py
train.py
infer.py
```

Changes karo:

```bash
git status
```

Files stage:

```bash
git add .
```

Commit:

```bash
git commit -m "Add initial U-Net segmentation pipeline"
```

Push:

```bash
git push -u origin feature/segmentation
```

Ab branch GitHub par aa jayegi.

---

# 7. Pull Request kab banana hai?

Jab feature reasonably complete ho aur tumne locally test kar liya ho.

Example:

```text
feature/segmentation
        ↓
       PR
        ↓
main
```

PR banane se pehle **latest remote `main` ke saath apni branch sync karna important hai**.

Yahin se tumhara original doubt aata hai.

---

# 8. Sabse important concept: `main` move karta rahega

Suppose initially:

```text
main: A → B
```

Soham ne branch banayi:

```text
main: A → B
             \
              S1 → S2
```

Meanwhile Vedant ne apna feature merge kar diya.

Ab remote `main`:

```text
main: A → B → V1 → V2
```

Lekin Soham ki branch:

```text
main: A → B
             \
              S1 → S2
```

Soham ki branch **main se behind hai**.

### Kya ye problem hai?

**Nahi.**

Branch ka `main` se behind hona automatically conflict ka matlab nahi hai.

Conflict tab hota hai jab Git ko same/similar code changes ko automatically combine karna difficult lage.

---

# 9. PR se pehle latest `main` kaise laayenge?

Yahan ek important distinction:

```text
origin/main
```

= GitHub par actual latest remote `main`

```text
main
```

= tumhari local `main`

Tumhari local `main` outdated ho sakti hai.

Isliye PR se pehle safest simple workflow:

```bash
git fetch origin
git checkout feature/your-branch
git merge origin/main
```

### `git fetch origin` kya karta hai?

Remote GitHub ki latest information locally laata hai.

Important:

> `fetch` tumhari working files ko automatically change nahi karta.

Uske baad:

```bash
git merge origin/main
```

latest remote `main` ko tumhari feature branch mein merge karta hai.

---

# 10. Conflict aaya toh?

Suppose:

```text
origin/main:
MODEL = "EfficientNet"

your branch:
MODEL = "ResNet50"
```

Git ko samajh nahi aayega ki kaunsa version rakhna hai.

Conflict milega.

Example:

```text
MODEL = "ResNet50"
MODEL = "EfficientNet"
```

Ab **tum apni feature branch par conflict resolve karoge**.

Correct code decide karo, conflict markers remove karo.

Then:

```bash
git add .
git commit -m "Resolve merge conflicts with main"
```

Test everything.

Then:

```bash
git push
```

---

# 11. Important: Conflict main mein nahi, pehle feature branch mein solve karna hai

Ye hamara major safety mechanism hai.

Wrong idea:

```text
feature branch
      ↓
PR
      ↓
main breaks
      ↓
panic
```

Better:

```text
feature branch
      ↓
merge latest origin/main
      ↓
resolve conflicts
      ↓
test
      ↓
push
      ↓
PR
      ↓
review
      ↓
merge
```

Isse conflict resolution **main ko affect kiye bina** hoti hai.

---

# 12. Kya GitHub automatically check karega?

Haan.

Agar tum PR create karte ho:

```text
feature/segmentation → main
```

GitHub check karega ki branch current `main` ke saath mergeable hai ya nahi.

Lekin best practice:

> **GitHub par PR banane se pehle locally latest `origin/main` merge karke conflicts resolve kar lo.**

Isse tum khud locally complete integration test kar sakte ho.

---

# 13. Ek important race condition

Suppose:

```text
10:00 AM
origin/main = A → B → C
```

Tumne apni branch mein latest main merge kar liya.

```text
A → B → C
          \
           X → Y
```

Phir 10:15 AM par kisi aur ka PR merge ho gaya:

```text
A → B → C → D
```

Tumhari branch ab phir se latest `main` se behind hai:

```text
A → B → C
          \
           X → Y
```

Isliye PR merge hone se pehle agar `main` move ho gaya, toh dobara sync karna pad sakta hai.

Again:

```bash
git fetch origin
git merge origin/main
```

Resolve → test → push.

---

# 14. Kya har 10 minute mein `main` sync karna hai?

**Nahi.**

Aisa kiya toh development se zyada Git update karoge.

Normal workflow:

```text
Start feature
      ↓
Work normally
      ↓
Other teammates merge their work
      ↓
Finish feature
      ↓
Before PR:
fetch + merge origin/main
      ↓
resolve conflicts if any
      ↓
test
      ↓
push
      ↓
PR
```

Agar tumhe kisi aur ke newly merged code ki zarurat hai, tab bhi `origin/main` sync kar sakte ho.

---

# 15. Humari project structure mein conflicts kahan likely hain?

Hamare project mein kaafi modules naturally separated hain:

```text
frontend/
ml/classification/
ml/segmentation/
ml/preprocessing/
ml/explainability/
simulink/
```

Agar alag log alag modules par kaam kar rahe hain, toh conflicts ka chance low hai.

### Low-risk examples

```text
Person A → ml/classification/
Person B → ml/segmentation/
Person C → frontend/
Person D → simulink/
```

Generally ye log ek doosre ki files touch nahi kar rahe.

### Higher-risk/shared files

Special attention:

```text
backend/app/services/pipeline.py
backend/app/api/routes_predict.py
backend/app/models/schemas.py
README.md
requirements.txt
docs/interfaces.md
deployment/docker-compose.yml
```

In files par multiple people ka kaam overlap kar sakta hai.

---

# 16. Sabse important: Interface contract

Hamare paas already:

```text
docs/interfaces.md
```

Isko seriously maintain karna.

Example conceptual flow:

```text
Frontend
   ↓
API
   ↓
Backend pipeline
   ↓
Preprocessing
   ↓
Classification / Segmentation
   ↓
Explainability
   ↓
Final response
   ↓
Frontend
```

Har module ko clear hona chahiye:

- Input kya hai?
- Output kya hai?
- Data format kya hai?
- Function/API ka naam kya hai?
- Expected error behavior kya hai?

Example:

```text
Classification input:
image

Classification output:
{
    label,
    confidence
}
```

Exact schema project ke actual requirements ke according decide hoga.

### Why?

Warna situation:

> "Mera model ready hai."

> "Output kya deta hai?"

> "Tensor."

> "...okay."

Aur phir aadha din integration mein chala jaata hai.

---

# 17. Golden Rules for the team

## Rule 1

**Never directly push to `main`.**

---

## Rule 2

**Always work on a feature branch.**

```bash
git checkout -b feature/<name>
```

---

## Rule 3

**Before PR, sync with latest remote main.**

```bash
git fetch origin
git merge origin/main
```

---

## Rule 4

**Conflicts apni feature branch mein resolve karo.**

Main ko conflict-resolution playground mat banao.

---

## Rule 5

**After resolving conflicts, test before PR.**

At minimum:

```bash
git status
```

Aur project ke relevant tests/run commands execute karo.

---

## Rule 6

**Small, meaningful commits rakho.**

Good:

```text
Add U-Net training pipeline
Add segmentation inference
Add mask post-processing
Fix image normalization
```

Bad:

```text
final
final2
final_final
final_final_REAL
please_work
```

Git commit history ko emotional diary mat banao.

---

## Rule 7

**Ek doosre ke module ko unnecessarily edit mat karo.**

Agar integration ke liye doosre module mein change chahiye:

> Pehle teammate ko inform karo.

---

## Rule 8

**Shared interfaces pehle decide karo.**

Especially:

```text
API schemas
model outputs
file formats
function signatures
```

---

# 18. Recommended workflow for every teammate

### Start of task

```bash
git checkout main
git pull origin main
git checkout -b feature/<your-feature>
```

### During development

```bash
git status
git add .
git commit -m "Meaningful commit message"
git push
```

### Before PR

```bash
git fetch origin
git merge origin/main
```

If conflict:

```text
Resolve
↓
git add .
↓
git commit
↓
Test
```

Then:

```bash
git push
```

### Finally

Create PR:

```text
feature/<your-feature>
          ↓
        main
```

Manmit reviews → merge.

---

# 19. What happens after someone else's PR is merged?

Suppose Tanvi's PR gets merged.

Remote:

```text
main → Tanvi's changes
```

Soham's local `main` may still be old.

**That's completely normal.**

Soham does NOT need to immediately update his local main just because Tanvi's PR merged.

When Soham needs latest main:

```bash
git fetch origin
git merge origin/main
```

into his feature branch.

---

# 20. Final mental model

Think of `main` as the team's **official shared notebook**.

Everyone gets their own rough notebook:

```text
Manmit → feature/manmit
Soham → feature/soham
Vedant → feature/vedant
Ninad → feature/ninad
Devyani → feature/devyani
Tanvi → feature/tanvi
```

Everyone works independently.

When someone is ready:

```text
rough notebook
     ↓
compare with latest official notebook
     ↓
fix differences
     ↓
test
     ↓
PR
     ↓
review
     ↓
official notebook (`main`)
```

The key idea:

> **`main` is shared, feature branches are isolated, PRs are the gate.**

---

# 21. Our final SIH Git setup

```text
                    PRIVATE REPOSITORY
                           │
                           ▼
                     main (PROTECTED)
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
 feature/frontend   feature/segmentation   feature/backend
        │                  │                  │
        │                  │                  │
        └────────────── PRs ──────────────────┘
                           │
                           ▼
                      MANMIT REVIEW
                           │
                           ▼
                         MERGE
                           │
                           ▼
                         main
```

### Team members

| Member | Role in Git workflow |
|---|---|
| **Manmit** | Repository owner + PR reviewer/merger |
| **Soham** | Collaborator + feature branches |
| **Vedant** | Collaborator + feature branches |
| **Ninad** | Collaborator + feature branches |
| **Devyani** | Collaborator + feature branches |
| **Tanvi** | Collaborator + feature branches |

---

# TL;DR

```text
Private repo
     ↓
6 collaborators
     ↓
No forks
     ↓
No direct main push
     ↓
Everyone creates feature branch
     ↓
Work independently
     ↓
Before PR:
git fetch origin
git merge origin/main
     ↓
Resolve conflicts locally
     ↓
Test
     ↓
Push
     ↓
PR → main
     ↓
Manmit reviews + merges
```

**That's it.**

Git ka purpose humein project banane mein help karna hai, project ke upar ek aur project banana nahi.
