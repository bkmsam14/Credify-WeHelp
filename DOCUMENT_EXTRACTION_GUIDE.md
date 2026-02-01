# Document Extraction Guide

## What the System Expects

The system uses **regex patterns** to extract data. Your document must contain **specific keywords followed by the value**.

### GENERIC Documents (Accepts ANY document)

Your simple PDF with "name" and "credit score" should work with GENERIC patterns. Here's what it's looking for:

#### 1. **Name/Applicant Name**
**Keywords it recognizes:**
- `name:` or `Name:` or `nom:`
- `client:` or `Client:`
- `applicant:` or `Applicant:`

**Examples that WORK:**
```
Name: John Doe
nom: Ahmed Ben Ali
Client: Sarah Smith
Applicant Name: Jane Doe
```

**Examples that DON'T WORK:**
```
JOHN DOE (no label)
Client Name: John (too much extra text)
```

---

#### 2. **Credit Score**
**Keywords it recognizes:**
- `credit:` or `Credit:`
- `score:` or `Score:`
- `crédit:` (French)

**Examples that WORK:**
```
Credit Score: 720
Credit: 680
Score: 750
crédit: 700
```

**Examples that DON'T WORK:**
```
720 (no label)
Your credit is good (text description, no number)
score-720 (needs colon or space)
```

---

#### 3. **Monthly Income**
**Keywords it recognizes:**
- `income:` or `Income:`
- `salary:` or `Salary:`
- `salaire:` (French)
- `revenu:` (French)

**Examples that WORK:**
```
Monthly Income: 3500
Income: 3500.00
Salary: 3500
Revenu mensuel: 3500
```

---

#### 4. **Savings/Balance**
**Keywords it recognizes:**
- `savings:` or `Savings:`
- `balance:` or `Balance:`
- `solde:` (French)
- `épargne:` (French)

**Examples that WORK:**
```
Savings Balance: 8500
Balance: 8500.50
Solde: 8500
```

---

#### 5. **Email**
**Format:** Must be a valid email address

**Examples that WORK:**
```
john@example.com
ahmed.benaali@bank.tn
user.name+tag@domain.co.uk
```

---

#### 6. **Phone Number**
**Keywords it recognizes:**
- `phone:` or `Phone:`
- `téléphone:` (French)
- `mobile:` or `Mobile:`

**Examples that WORK:**
```
Phone: +216 25 123 456
Mobile: 25123456
Phone: (25) 123-4567
```

---

#### 7. **Address**
**Keywords it recognizes:**
- `address:` or `Address:`
- `adresse:` (French)
- `rue:` or `street:` (French)

**Examples that WORK:**
```
Address: 123 Main Street, Tunis
Adresse: Rue de l'Église 45, Sfax
Street: Avenue Mohamed V
```

---

## How to Make Your PDF Work

### ✅ DO THIS:
Create a PDF with clear **label: value** format:

```
BANK BILL
Name: John Doe
Credit Score: 720
Monthly Income: 3500
Savings Balance: 8500
```

### ❌ DON'T DO THIS:
```
BANK BILL
John Doe
720
3500
8500
```
(No labels = no extraction)

---

## Test Your Document

Before uploading, check your PDF has:
1. **At least ONE matching keyword** from the list above
2. **A colon (`:`) or space after the keyword**
3. **The actual value right after**

### Example WORKING PDF:
```
==================
APPLICANT DETAILS
==================
Name: Ahmed Mohamed
Credit Score: 750
Monthly Income: 4500
Savings Balance: 15000
Email: ahmed@email.com
Phone: +216 25 123 456
Address: 123 Main Street, Tunis
==================
```

### Why Your PDF Might Fail:
- ❌ No colons: `BANK BILL 2 fields name and credit score` (just text, no labels)
- ❌ Different keywords: `Applicant ID:`, `Score Result:` (not in the pattern list)
- ❌ No numbers: `High credit score` (not a numeric value)
- ❌ Missing labels: Just `John Doe` and `720` on separate lines

---

## Summary: What Gets Extracted

| Field | Keywords | Format | Example |
|-------|----------|--------|---------|
| **Name** | name, nom, client, applicant | `keyword: value` | `Name: John Doe` |
| **Credit Score** | credit, score, crédit | `keyword: 3-4 digits` | `Credit: 720` |
| **Income** | income, salary, revenu, salaire | `keyword: number` | `Income: 3500` |
| **Savings** | savings, balance, solde, épargne | `keyword: number` | `Savings: 8500` |
| **Email** | (auto-detected) | `user@domain.com` | `john@bank.tn` |
| **Phone** | phone, téléphone, mobile | `keyword: digits` | `Phone: 25123456` |
| **Address** | address, adresse, rue, street | `keyword: text` | `Address: 123 Main St` |

---

## Need Help?

Upload a PDF with this exact format and it WILL work:
```
Name: Test User
Credit Score: 750
Monthly Income: 5000
```

That's all you need!
