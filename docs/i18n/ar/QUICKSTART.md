> **Language:** العربية (Arabic)  
> **Authoritative version:** [README.md](../../../README.md) and [System Overview](../../architecture/SYSTEM_OVERVIEW.md)  
> **Last synced:** 2026-11-01

---

# البدء السريع — АРХОН

## المتطلبات

- Python 3.11 أو أحدث (وفق نطاق الإصدارات المحدد في `pyproject.toml`).
- Git.
- اتصال بالإنترنت لتنزيل المستودع واعتماديات التثبيت.
- TSAR اختياري للتطوير المحلي العام، لكنه مطلوب عندما تتطلب بوابة المشروع تحققاً أمنياً مفوضاً إليه.

## التثبيت

### Linux وmacOS

```bash
git clone https://github.com/mohamedelghazali/Apxoh.git
cd Apxoh
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

### Windows PowerShell

```powershell
git clone https://github.com/mohamedelghazali/Apxoh.git
Set-Location Apxoh
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

## التحقق من التثبيت

```bash
arkhon version
arkhon validate
```

يعرض الأمر الأول إصدار CLI. ويتحقق الأمر الثاني من عناصر التحقق التي يدعمها الإصدار المثبت؛ ولا يعني نجاحه وحده أن المشروع اجتاز جميع بوابات الجودة أو الأمن أو الجاهزية للإنتاج.

## أول استخدام

### 1. استكشف مشروعاً

```bash
arkhon inspect /path/to/project
```

استبدل المسار بمجلد المشروع المستهدف. استخدم `.` لفحص مجلد العمل الحالي.

### 2. تحقق من نطاق محدد

```bash
arkhon verify /path/to/project --domain testing
```

نفّذ ذلك بعد مراجعة الخيارات المتاحة في إصدار CLI المثبت. نتيجة التحقق تخص الأدوات والأدلة التي نُفذت فعلياً فقط.

### 3. التقييم والتقرير

توجد في المشروع مكونات للتقييم وإنتاج التقارير، لكن تفاصيل الخيارات والمخرجات تعتمد على إصدار CLI؛ راجع `arkhon --help` و`arkhon assess --help` و`arkhon report --help` قبل الاعتماد على أي مسار أو صيغة إخراج.

## المفاهيم الأساسية

| المفهوم | المعنى |
| :--- | :--- |
| **Rule** | قاعدة هندسية تصف متطلباً قابلاً للتقييم |
| **Gate** | بوابة قرار في دورة حياة المشروع |
| **Evidence** | سجل يصف تحققاً ونتيجته ومصادره |
| **Finding** | نتيجة مرتبطة بقاعدة أو شرط |
| **Score** | قيمة تقييم مجمعة وفق أوزان محددة |
| **Level** | تصنيف للتقييم، وليس بديلاً عن قرار البوابة |
| **BLOCKED** | تعذر إصدار حكم إيجابي بسبب نقص أو تعذر التحقق |

## مراجع مفيدة

| الموضوع | الملف |
| :--- | :--- |
| المعمارية | `docs/architecture/SYSTEM_OVERVIEW.md` |
| كتابة قاعدة | `docs/rule-authoring/HOW_TO_WRITE_A_RULE.md` |
| أمثلة القواعد | `docs/rule-authoring/EXAMPLES.md` |
| تبنّي АРХОН في وكيل | `docs/agent-adoption/ADOPTION_GUIDE.md` |
| نموذج التهديد | `docs/threat-model/ARKHON_THREAT_MODEL.md` |
| المصطلحات | `docs/architecture/GLOSSARY.md` |

---

**ملاحظة:** هذه ترجمة عربية مرافقة؛ النسخة الإنجليزية هي المرجع عند وجود اختلاف.
