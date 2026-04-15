# 🧠 Intelligent Code Error Explainer (C Language)

## 📌 Overview

The **Intelligent Code Error Explainer** is a developer-assist tool designed to simplify compiler errors for C programs. It analyzes GCC compiler diagnostics and converts them into **human-readable explanations**, helping beginners and developers understand and fix errors efficiently.

The system combines:

* Compiler-based error detection (GCC)
* Machine Learning-based classification
* Rule-based fallback explanations

---

## 🎯 Problem Statement

Compiler errors (especially from GCC) are often:

* Hard to understand
* Technical and verbose
* Unfriendly for beginners

This project solves that by:
👉 Translating raw compiler errors into simple explanations
👉 Suggesting possible fixes
👉 Improving learning and debugging speed

---

## 🚀 Features

* ✅ Compile and analyze C code dynamically
* ✅ Extract line & column-level error details
* ✅ ML-based error classification
* ✅ Human-readable explanations
* ✅ Suggested fixes for each error
* ✅ Fallback rule-based system (if ML model unavailable)
* ✅ Automatic execution after successful compilation
* ✅ Web-based UI for interaction

---

## 🛠️ Tech Stack

### 🔹 Backend

* Python
* FastAPI
* GCC (C Compiler)
* Subprocess handling

### 🔹 Machine Learning

* Scikit-learn (Joblib model)
* Custom trained classifier (`gcc_explainer.joblib`)

### 🔹 Frontend

* HTML
* CSS
* JavaScript (Vanilla JS)

---

## 🏗️ System Architecture

```
User Input (C Code)
        ↓
Frontend (HTML + JS)
        ↓
FastAPI Backend
        ↓
GCC Compiler Execution
        ↓
Error Output Parsing (gcc_parse.py)
        ↓
ML Model / Rule-Based Explainer
        ↓
Structured Explanation Response
        ↓
Frontend Display
```

---

## 🔄 Architecture Flow (Step-by-Step)

1. User enters C code in UI
2. Code is sent to FastAPI backend
3. Backend writes code to temporary file
4. GCC compiler is invoked
5. Compiler output is captured
6. Errors are parsed into structured format
7. Each error is passed to:

   * ML model (if available) OR
   * Rule-based explanation system
8. Explanation + fix suggestions generated
9. Response returned to frontend
10. If compilation succeeds → program executes

---

## 🤖 Algorithms Used

### 1️⃣ Error Classification (ML Model)

* Input: GCC diagnostic message
* Output: Error category (e.g., syntax, undefined reference)
* Model: Pre-trained classifier (`joblib`)

---

### 2️⃣ Rule-Based Fallback System

If ML model is unavailable:

* Uses keyword matching
* Maps error patterns → predefined explanations

---

### 3️⃣ GCC Output Parsing Algorithm

**Workflow:**

1. Capture raw GCC output
2. Extract:

   * File name
   * Line number
   * Column
   * Error message
3. Convert into structured `Diagnostic` object

---

### 4️⃣ Explanation Generation Flow

```
GCC Error → Parsed Diagnostic
        ↓
Check ML Model Availability
        ↓
IF available → Predict Category
ELSE → Use Rule Matching
        ↓
Fetch Explanation from Catalog
        ↓
Return:
- Plain explanation
- Likely cause
- Suggested fix
```

---

## 📁 Project Structure

```
backend/
│
├── main.py                # FastAPI application
├── gcc_parse.py          # GCC output parser
├── local_explain.py      # ML + rule-based logic
├── explainer_catalog.py  # Predefined explanations
├── train_explainer.py    # Model training script
│
├── models/
│   └── gcc_explainer.joblib
│
├── static/
│   ├── index.html
│   ├── style.css
│   └── app.js
│
├── requirements.txt
└── run.bat
```

---

## ⚙️ Installation & Setup

### 1️⃣ Clone Repository

```bash
git clone https://github.com/alwayslohith9999/INTELLIGENT-CODE-EXPLAINER.git
cd INTELLIGENT-CODE-EXPLAINER
```

---

### 2️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

---

### 3️⃣ Install GCC

Make sure GCC is installed:

```bash
gcc --version
```

---

### 4️⃣ Run Backend Server

```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

---

### 5️⃣ Open in Browser

```
http://127.0.0.1:8000
```

---

## 🧪 Usage

1. Enter C code in the editor
2. Click **Analyze**
3. View:

   * Errors
   * Explanation
   * Suggested fixes

---

## 📊 Example Output

**Input Code:**

```c
printf("Hello")
```

**Output:**

* Error: Missing semicolon
* Explanation: Statement not properly terminated
* Fix: Add `;` at end

---

## 🔮 Future Enhancements

* 🔹 Support for multiple languages (Python, Java)
* 🔹 Deep Learning-based explanation model
* 🔹 Code auto-correction
* 🔹 IDE plugin integration
* 🔹 Real-time error detection

---

* GitHub: https://github.com/alwayslohith9999

---

## ⭐ Conclusion

This project bridges the gap between **compiler diagnostics and human understanding**, making debugging easier, faster, and more educational.

---
