import os
import random
import asyncio
from datetime import datetime, time
from supabase import create_client
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ===================== إعدادات البيئة =====================
TOKEN = os.getenv("BOT_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# ===================== إعدادات الإرسال اليومي =====================
DAILY_QUESTIONS_MIN = 20
DAILY_QUESTIONS_MAX = 50
SEND_HOUR = 10  # الساعة التي تُرسل فيها الأسئلة (10 صباحاً)
SEND_MINUTE = 0

# ===================== تهيئة Supabase =====================
if SUPABASE_URL and SUPABASE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("✅ تم الاتصال بـ Supabase بنجاح")
else:
    print("❌ Supabase غير مضبوط")
    supabase = None

# ===================== الأسئلة المدمجة (100 سؤال) =====================
DEFAULT_QUESTIONS = [
    # Pi Network - أساسيات
    {"question": "متى تم إطلاق تطبيق Pi Network رسمياً؟", "options": ["2018", "2019", "2020", "2021"], "correct": "B", "explanation": "تم إطلاق Pi Network في 14 مارس 2019 (يوم باي)."},
    {"question": "ما هو الهدف الرئيسي من مشروع Pi Network؟", "options": ["تعدين البيتكوين", "إنشاء عملة رقمية يمكن تعدينها من الهاتف", "تداول العملات", "إنشاء منصة ألعاب"], "correct": "B", "explanation": "الهدف هو جعل التعدين الرقمي متاحاً للجميع عبر الهواتف الذكية."},
    {"question": "من هم مؤسسو Pi Network؟", "options": ["فيتاليك بوتيرين", "د. نيكولاس كوكاليس ود. تشينغكياو فان", "تشانغ بينغ", "جاك دورسي"], "correct": "B", "explanation": "المؤسسون هم د. نيكولاس كوكاليس ود. تشينغكياو فان."},
    {"question": "ما هو شعار Pi Network؟", "options": ["المستقبل هو الآن", "باي من أجل الشعب", "العملة الرقمية للجميع", "ثورة البلوكشين"], "correct": "B", "explanation": "شعار Pi Network هو 'Pi for the People'."},
    # البلوكشين
    {"question": "ما هي تقنية البلوكشين؟", "options": ["قاعدة بيانات مركزية", "سجل رقمي موزع وآمن", "شبكة اجتماعية", "نظام تشغيل"], "correct": "B", "explanation": "البلوكشين هو سجل رقمي موزع وآمن يسجل المعاملات."},
    {"question": "ما هو بروتوكول الإجماع المستخدم في Pi Network؟", "options": ["إثبات العمل (PoW)", "إثبات الحصة (PoS)", "بروتوكول ستيلار (SCP)", "إثبات السلطة"], "correct": "C", "explanation": "Pi يستخدم بروتوكول ستيلار (Stellar Consensus Protocol)."},
    {"question": "ما هي السلسلة الكتلية (Blockchain)؟", "options": ["سلسلة من الكتل تحتوي على بيانات", "شبكة من الحواسيب", "عملة رقمية", "منصة تداول"], "correct": "A", "explanation": "البلوكشين هي سلسلة من الكتل تحتوي على بيانات المعاملات."},
    {"question": "ما هي اللامركزية في البلوكشين؟", "options": ["تحكم جهة واحدة", "توزيع السلطة بين جميع المشاركين", "نظام مركزي", "لا شيء مما سبق"], "correct": "B", "explanation": "اللامركزية تعني توزيع السلطة والتحكم بين جميع المشاركين."},
    {"question": "ما هو التعدين في البلوكشين؟", "options": ["استخراج الذهب", "التحقق من المعاملات وإضافتها إلى السلسلة", "شراء العملات", "بيع العملات"], "correct": "B", "explanation": "التعدين هو عملية التحقق من المعاملات وإضافتها إلى البلوكشين."},
    {"question": "ما هو الفرق بين البلوكشين العامة والخاصة؟", "options": ["لا يوجد فرق", "العامة مفتوحة للجميع، الخاصة مقيدة", "العامة أسرع", "الخاصة أكثر أمناً"], "correct": "B", "explanation": "البلوكشين العامة مفتوحة للجميع، بينما الخاصة تتطلب إذناً."},
    # العقد (Nodes)
    {"question": "ما هي العقدة (Node) في البلوكشين؟", "options": ["جهاز كمبيوتر متصل بالشبكة يتحقق من المعاملات", "عملة رقمية", "تطبيق هاتف", "خادم مركزي"], "correct": "A", "explanation": "العقدة هي جهاز كمبيوتر متصل بالشبكة يقوم بالتحقق من المعاملات."},
    {"question": "ما هو دور عقد Pi Network؟", "options": ["تعدين العملات فقط", "التحقق من المعاملات والحفاظ على الشبكة", "بيع العملات", "تطوير التطبيقات"], "correct": "B", "explanation": "دور العقد هو التحقق من المعاملات والحفاظ على أمن الشبكة."},
    {"question": "كم عدد العقد المطلوبة لتشغيل شبكة Pi؟", "options": ["10 عقد", "100 عقد", "آلاف العقد اللامركزية", "عقدة واحدة"], "correct": "C", "explanation": "Pi يعتمد على آلاف العقد اللامركزية."},
    {"question": "ما هي متطلبات تشغيل عقدة Pi؟", "options": ["هاتف ذكي", "حاسوب مع اتصال إنترنت", "خادم سحابي", "جهاز تعدين خاص"], "correct": "B", "explanation": "تحتاج إلى حاسوب مع اتصال إنترنت مستقر."},
    # النظام البيئي
    {"question": "ما هو متصفح Pi Browser؟", "options": ["متصفح ويب عادي", "متصفح مخصص لتطبيقات Pi اللامركزية", "تطبيق للمحادثة", "منصة ألعاب"], "correct": "B", "explanation": "Pi Browser هو متصفح مخصص لتطبيقات Pi اللامركزية."},
    {"question": "ما هي محفظة Pi Wallet؟", "options": ["محفظة لتخزين البيتكوين", "محفظة رقمية لتخزين عملات Pi", "تطبيق دفع", "بطاقة ائتمان"], "correct": "B", "explanation": "محفظة Pi Wallet هي محفظة رقمية لحفظ عملات Pi."},
    {"question": "ما هو النظام البيئي لـ Pi Network؟", "options": ["مجموعة التطبيقات والخدمات المبنية على Pi", "منصة تداول", "مؤتمر سنوي", "مركز تدريب"], "correct": "A", "explanation": "النظام البيئي يشمل جميع التطبيقات والخدمات التي تعتمد على Pi."},
    {"question": "ما هي تطبيقات Pi Ecosystem؟", "options": ["ألعاب ومنصات اجتماعية", "تطبيقات مالية وخدمات لامركزية", "كل ما سبق", "لا شيء مما سبق"], "correct": "C", "explanation": "تشمل التطبيقات المالية والاجتماعية والألعاب."},
    # ترحيل العملات
    {"question": "ما هو Mainnet في Pi Network؟", "options": ["شبكة اختبار", "الشبكة الرئيسية", "تطبيق للهاتف", "منصة تداول"], "correct": "B", "explanation": "Mainnet هي الشبكة الرئيسية التي تعمل عليها العملات الحقيقية."},
    {"question": "ما هو ترحيل العملات (Migration)؟", "options": ["نقل العملات من Testnet إلى Mainnet", "بيع العملات", "شراء العملات", "تعدين جديد"], "correct": "A", "explanation": "الترحيل هو نقل العملات من شبكة الاختبار إلى الشبكة الرئيسية."},
    {"question": "ما هو Open Mainnet؟", "options": ["الشبكة الرئيسية المفتوحة للجميع", "شبكة مغلقة", "شبكة اختبار", "مرحلة التطوير"], "correct": "A", "explanation": "Open Mainnet هي الشبكة الرئيسية المفتوحة للجميع."},
    {"question": "متى تم إطلاق Mainnet لـ Pi Network؟", "options": ["2021", "2022", "2023", "لم يتم إطلاقها بعد"], "correct": "A", "explanation": "تم إطلاق Mainnet في ديسمبر 2021."},
    # KYC و KYB
    {"question": "ما هو KYC في Pi Network؟", "options": ["معرفة العميل", "إثبات الهوية", "فحص خلفية", "كل ما سبق"], "correct": "D", "explanation": "KYC هو إجراء للتحقق من هوية المستخدمين."},
    {"question": "ما هو KYB؟", "options": ["معرفة الأعمال", "التحقق من المؤسسات التجارية", "فحص الشركات", "كل ما سبق"], "correct": "D", "explanation": "KYB هو التحقق من المؤسسات التجارية."},
    {"question": "لماذا يتطلب Pi Network KYC؟", "options": ["للأمان ومنع الاحتيال", "للإعلانات", "للبيع", "لا سبب"], "correct": "A", "explanation": "KYC يمنع الاحتيال ويضمن أمان الشبكة."},
    {"question": "ما هي مستندات KYC المطلوبة في Pi؟", "options": ["بطاقة هوية أو جواز سفر", "فاتورة كهرباء", "صورة شخصية", "كل ما سبق"], "correct": "A", "explanation": "يتم قبول بطاقة الهوية أو جواز السفر كوثائق رئيسية."},
    {"question": "هل KYC إلزامي في Pi Network؟", "options": ["نعم، للوصول إلى Mainnet", "لا", "للأعضاء فقط", "للمطورين فقط"], "correct": "A", "explanation": "KYC إلزامي لجميع المستخدمين للوصول إلى Mainnet."},
    # عملات Layer 1
    {"question": "ما هو تعريف العملة من نوع Layer 1؟", "options": ["طبقة أساسية من البلوكشين", "طبقة ثانوية", "تطبيق لامركزي", "لا شيء مما سبق"], "correct": "A", "explanation": "العملات من نوع Layer 1 هي الطبقة الأساسية للبلوكشين مثل Pi و Bitcoin."},
    {"question": "هل Pi Network من نوع Layer 1؟", "options": ["نعم", "لا", "غير معروف", "Layer 2"], "correct": "A", "explanation": "Pi Network هو عملة Layer 1."},
    {"question": "ما هي أمثلة على عملات Layer 1؟", "options": ["Bitcoin, Ethereum, Pi", "Uniswap, PancakeSwap", "USDC, USDT", "BNB, MATIC"], "correct": "A", "explanation": "Bitcoin و Ethereum و Pi كلها Layer 1."},
    {"question": "ما هو الفرق بين Layer 1 و Layer 2؟", "options": ["Layer 1 أساسية، Layer 2 فوقها", "لا يوجد فرق", "Layer 2 هي الأساسية", "كلاهما متشابهان"], "correct": "A", "explanation": "Layer 1 هي الطبقة الأساسية، Layer 2 مبنية فوقها لتوسيع القدرات."},
    {"question": "ما هي ميزة عملات Layer 1؟", "options": ["أمن عالٍ ولامركزية", "سرعة عالية", "رسوم منخفضة", "كل ما سبق"], "correct": "A", "explanation": "الأمن واللامركزية هما الميزة الرئيسية لـ Layer 1."},
    # تطورات الشبكة
    {"question": "كم عدد مستخدمي Pi Network حالياً؟", "options": ["أكثر من 10 ملايين", "أكثر من 30 مليون", "أكثر من 50 مليون", "أكثر من 100 مليون"], "correct": "C", "explanation": "وصل عدد مستخدمي Pi إلى أكثر من 50 مليون مستخدم."},
    {"question": "ما هو إنجاز Pi Network الأبرز؟", "options": ["أكبر مجتمع تعدين هاتفي", "أسرع بلوكشين", "أرخص رسوم", "كل ما سبق"], "correct": "A", "explanation": "Pi يمتلك أكبر مجتمع تعدين عبر الهواتف الذكية."},
    {"question": "ما هي المرحلة القادمة لـ Pi Network؟", "options": ["Open Mainnet", "شبكة جديدة", "بيع العملات", "إيقاف المشروع"], "correct": "A", "explanation": "المرحلة القادمة هي Open Mainnet."},
    {"question": "هل Pi Network مشروع مفتوح المصدر؟", "options": ["نعم", "لا", "جزئياً", "غير معروف"], "correct": "A", "explanation": "Pi Network مفتوح المصدر جزئياً للشفافية."},
    {"question": "ما هي شراكة Pi Network مع Stellar؟", "options": ["استخدام بروتوكول Stellar", "شراء Stellar", "دمج العملات", "لا توجد شراكة"], "correct": "A", "explanation": "Pi يستخدم بروتوكول Stellar Consensus Protocol."},
    # إنجازات وتاريخ
    {"question": "في أي عام تجاوز Pi Network 10 ملايين مستخدم؟", "options": ["2019", "2020", "2021", "2022"], "correct": "B", "explanation": "تجاوز Pi 10 ملايين مستخدم في عام 2020."},
    {"question": "ما هو اسم التطبيق الرسمي لـ Pi Network؟", "options": ["Pi App", "Pi Network", "Pi Browser", "Pi Wallet"], "correct": "B", "explanation": "التطبيق الرسمي يسمى Pi Network."},
    {"question": "ما هي رؤية Pi Network لعام 2025؟", "options": ["Open Mainnet", "100 مليون مستخدم", "منصة تطبيقات متكاملة", "كل ما سبق"], "correct": "D", "explanation": "الرؤية تشمل Open Mainnet و100 مليون مستخدم ومنصة تطبيقات."},
    {"question": "ما هو أكبر تحدٍ واجه Pi Network؟", "options": ["تقنية البلوكشين", "ثقة المستخدمين", "الامتثال التنظيمي", "كل ما سبق"], "correct": "D", "explanation": "التحديات تشمل التقنية والثقة والامتثال التنظيمي."},
    {"question": "ما هي ميزة Pi عن العملات الأخرى؟", "options": ["التعدين من الهاتف", "مجتمع كبير", "رسوم صفر", "كل ما سبق"], "correct": "D", "explanation": "Pi يتميز بالتعدين من الهاتف والمجتمع الكبير والرسوم المنخفضة."},
    # التطبيقات والاستخدامات
    {"question": "ما هي استخدامات عملة Pi؟", "options": ["الدفع مقابل السلع والخدمات", "التداول", "الاستثمار", "كل ما سبق"], "correct": "D", "explanation": "يمكن استخدام Pi للدفع والتداول والاستثمار."},
    {"question": "هل يمكن شراء Pi من البورصات حالياً؟", "options": ["نعم", "لا، فقط عبر التعدين", "في بعض البورصات", "غير معروف"], "correct": "B", "explanation": "حالياً، يتم الحصول على Pi عبر التعدين فقط."},
    {"question": "ما هي قيمة Pi الحالية؟", "options": ["قيمة غير محددة بعد", "1 دولار", "10 دولارات", "100 دولار"], "correct": "A", "explanation": "قيمة Pi لم تحدد بعد حتى Open Mainnet."},
    {"question": "ما هي الفوائد من امتلاك Pi؟", "options": ["شراء منتجات رقمية", "استثمار مستقبلي", "المشاركة في المجتمع", "كل ما سبق"], "correct": "D", "explanation": "الفوائد تشمل الشراء والاستثمار والمشاركة."},
]

# ===================== دوال قاعدة البيانات =====================

def initialize_questions():
    """إضافة الأسئلة المدمجة إذا كانت قاعدة البيانات فارغة"""
    if not supabase:
        return
    try:
        res = supabase.table("quiz_questions").select("id", count="exact").execute()
        if res.count == 0:
            print("📝 جاري إضافة الأسئلة المدمجة...")
            for q in DEFAULT_QUESTIONS:
                supabase.table("quiz_questions").insert({
                    "question": q["question"],
                    "option_a": q["options"][0],
                    "option_b": q["options"][1],
                    "option_c": q["options"][2],
                    "option_d": q["options"][3],
                    "correct_answer": q["correct"],
                    "explanation": q.get("explanation", "")
                }).execute()
            print(f"✅ تم إضافة {len(DEFAULT_QUESTIONS)} سؤال مدمج.")
    except Exception as e:
        print(f"⚠️ خطأ في إضافة الأسئلة: {e}")

def get_all_questions():
    if not supabase: return []
    res = supabase.table("quiz_questions").select("*").execute()
    return res.data if res.data else []

def get_random_questions(limit: int):
    questions = get_all_questions()
    if not questions: return []
    random.shuffle(questions)
    return questions[:min(limit, len(questions))]

def get_user(user_id: int):
    if not supabase: return None
    res = supabase.table("quiz_users").select("*").eq("user_id", user_id).execute()
    return res.data[0] if res.data else None

def create_user(user_id: int, first_name: str, username: str = ""):
    if not supabase: return
    supabase.table("quiz_users").insert({
        "user_id": user_id,
        "first_name": first_name,
        "username": username
    }).execute()

def update_user_stats(user_id: int, correct: bool, points: int = 10):
    if not supabase: return
    user = get_user(user_id)
    if not user: return
    new_correct = user.get("correct_answers", 0) + (1 if correct else 0)
    new_wrong = user.get("wrong_answers", 0) + (0 if correct else 1)
    new_points = user.get("total_points", 0) + (points if correct else 0)
    supabase.table("quiz_users").update({
        "correct_answers": new_correct,
        "wrong_answers": new_wrong,
        "total_points": new_points,
        "last_answered": datetime.now().date().isoformat()
    }).eq("user_id", user_id).execute()

def save_answer_history(user_id: int, question_id: int, answer: str, is_correct: bool):
    if not supabase: return
    supabase.table("quiz_history").insert({
        "user_id": user_id,
        "question_id": question_id,
        "answer": answer,
        "is_correct": is_correct
    }).execute()

def get_leaderboard(limit: int = 10):
    if not supabase: return []
    res = supabase.table("quiz_users").select("user_id, first_name, username, total_points, correct_answers").order("total_points", desc=True).limit(limit).execute()
    return res.data if res.data else []

# ===================== إدارة المجموعات =====================

def register_group(chat_id: int):
    """تسجيل معرف المجموعة في جدول quiz_groups"""
    if not supabase: return
    try:
        # نتحقق إذا كانت المجموعة مسجلة مسبقاً
        res = supabase.table("quiz_groups").select("chat_id").eq("chat_id", chat_id).execute()
        if not res.data:
            supabase.table("quiz_groups").insert({"chat_id": chat_id}).execute()
            print(f"✅ تم تسجيل المجموعة {chat_id}")
    except Exception as e:
        print(f"⚠️ خطأ في تسجيل المجموعة: {e}")

def get_all_groups():
    """جلب جميع المجموعات المسجلة"""
    if not supabase: return []
    try:
        res = supabase.table("quiz_groups").select("chat_id").execute()
        return [row['chat_id'] for row in res.data] if res.data else []
    except Exception as e:
        print(f"⚠️ خطأ في جلب المجموعات: {e}")
        return []

# ===================== إرسال الأسئلة اليومية =====================

async def send_daily_questions(context: ContextTypes.DEFAULT_TYPE):
    """إرسال أسئلة يومية إلى جميع المجموعات المسجلة"""
    groups = get_all_groups()
    if not groups:
        print("⚠️ لا توجد مجموعات مسجلة لإرسال الأسئلة.")
        return

    # جلب جميع الأسئلة
    all_questions = get_all_questions()
    if not all_questions:
        print("⚠️ لا توجد أسئلة في قاعدة البيانات.")
        return

    for chat_id in groups:
        # عدد أسئلة عشوائي بين 20 و 50
        num_questions = random.randint(DAILY_QUESTIONS_MIN, DAILY_QUESTIONS_MAX)
        # اختيار أسئلة عشوائية (يمكن أن تتكرر في مجموعات مختلفة، لكننا نضمن عدم التكرار داخل المجموعة نفسها)
        shuffled = all_questions.copy()
        random.shuffle(shuffled)
        selected = shuffled[:min(num_questions, len(shuffled))]

        # إرسال الأسئلة واحدة تلو الأخرى مع تأخير بسيط
        for idx, q in enumerate(selected):
            # بناء الأزرار
            keyboard = [
                [InlineKeyboardButton("🔵 A", callback_data=f"daily_{q['id']}_A"),
                 InlineKeyboardButton("🟢 B", callback_data=f"daily_{q['id']}_B")],
                [InlineKeyboardButton("🟡 C", callback_data=f"daily_{q['id']}_C"),
                 InlineKeyboardButton("🔴 D", callback_data=f"daily_{q['id']}_D")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            try:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"🧠 <b>سؤال اليوم ({idx+1}/{len(selected)})</b>\n\n"
                         f"{q['question']}\n\n"
                         f"🅰️ {q['option_a']}\n"
                         f"🅱️ {q['option_b']}\n"
                         f"🅲️ {q['option_c']}\n"
                         f"🅳️ {q['option_d']}",
                    parse_mode="HTML",
                    reply_markup=reply_markup
                )
                await asyncio.sleep(2)  # تأخير بين الأسئلة لتجنب الإغراق
            except Exception as e:
                print(f"❌ فشل إرسال السؤال إلى {chat_id}: {e}")

        print(f"✅ تم إرسال {len(selected)} سؤالاً إلى المجموعة {chat_id}")

# ===================== معالجة إجابات الأسئلة اليومية =====================

async def handle_daily_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = query.from_user
    user_id = user.id
    data = query.data

    if not data.startswith("daily_"):
        return

    parts = data.split("_")
    if len(parts) < 3:
        return

    question_id = int(parts[1])
    user_answer = parts[2]

    # جلب السؤال من قاعدة البيانات
    if not supabase:
        return
    res = supabase.table("quiz_questions").select("*").eq("id", question_id).execute()
    if not res.data:
        return
    question_data = res.data[0]
    correct = question_data['correct_answer']
    is_correct = (user_answer == correct)

    # تحديث إحصائيات المستخدم
    if not get_user(user_id):
        create_user(user_id, user.first_name or "مستخدم", user.username or "")
    update_user_stats(user_id, is_correct, 10)
    save_answer_history(user_id, question_id, user_answer, is_correct)

    # إرسال النتيجة
    await query.edit_message_text(
        f"{'✅ صحيح! 🎉' if is_correct else f'❌ خطأ! الإجابة الصحيحة هي {correct}'}\n\n"
        f"📖 {question_data.get('explanation', '')}\n\n"
        f"👤 {user.first_name} - {'+10 نقاط' if is_correct else '0 نقاط'}",
        parse_mode="HTML"
    )

# ===================== أوامر البوت الأساسية =====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not get_user(user.id):
        create_user(user.id, user.first_name or "مستخدم", user.username or "")

    await update.message.reply_text(
        f"🧠 <b>مرحباً {user.first_name}!</b>\n\n"
        "🌟 <b>أهلاً بك في Pi Quiz</b>\n"
        "🏆 اختبر معرفتك عن <b>Pi Network</b>!\n\n"
        "📌 <b>الأوامر المتاحة:</b>\n"
        "▫️ /quiz [عدد] - بدء الاختبار (1-100 سؤال)\n"
        "▫️ /leaderboard - لوحة المتصدرين 🏆\n"
        "▫️ /stats - عرض إحصائياتك 📊\n"
        "▫️ /help - عرض المساعدة ℹ️\n\n"
        "📢 <b>ميزة جديدة:</b>\n"
        "• يتم إرسال 20-50 سؤال يومياً في المجموعات.\n"
        "• أجب مباشرة عبر الأزرار في المجموعة.\n\n"
        "⏳ <b>لديك 60 ثانية</b> لكل سؤال!\n"
        "💡 الإجابة الصحيحة = <b>10 نقاط</b> 🎯",
        parse_mode="HTML"
    )

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 <b>دليل استخدام Pi Quiz</b>\n\n"
        "▫️ /quiz [عدد] - بدء الاختبار (1-100 سؤال)\n"
        "▫️ /leaderboard - عرض أفضل اللاعبين 🏆\n"
        "▫️ /stats - عرض إحصائياتك 📊\n"
        "▫️ /start - الصفحة الرئيسية 🏠\n\n"
        "📢 <b>الأسئلة اليومية في المجموعات:</b>\n"
        "• تُرسل 20-50 سؤالاً يومياً.\n"
        "• أجب بالضغط على الزر المناسب.\n"
        "• كل إجابة صحيحة = 10 نقاط.\n\n"
        "⏳ <b>نظام التوقيت:</b>\n"
        "• 60 ثانية للإجابة على كل سؤال.\n"
        "• عند انتهاء الوقت، يظهر الجواب الصحيح.\n\n"
        "🏅 <b>المستويات:</b>\n"
        "📗 0-50 نقطة: مبتدئ\n"
        "📘 51-100 نقطة: متعلم\n"
        "📙 101-200 نقطة: خبير\n"
        "🏅 201+ نقطة: أسطورة",
        parse_mode="HTML"
    )

async def quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id

    if not get_user(user_id):
        create_user(user_id, user.first_name or "مستخدم", user.username or "")

    args = context.args
    limit = 1
    if args:
        try:
            limit = int(args[0])
            if limit < 1: limit = 1
            elif limit > 100: limit = 100
        except ValueError:
            await update.message.reply_text("⚠️ الرجاء إدخال عدد صحيح.\nمثال: /quiz 10")
            return

    questions = get_random_questions(limit)
    if not questions:
        await update.message.reply_text(
            "❌ لا توجد أسئلة حالياً. يرجى المحاولة لاحقاً."
        )
        return

    context.user_data['quiz_queue'] = questions
    context.user_data['quiz_index'] = 0
    context.user_data['quiz_correct'] = 0
    context.user_data['quiz_total'] = len(questions)
    context.user_data['quiz_timer_job'] = None

    await send_question(update, context, chat_id=update.effective_chat.id)

async def send_question(update: Update, context: ContextTypes.DEFAULT_TYPE, chat_id: int = None):
    if chat_id is None:
        chat_id = update.effective_chat.id

    index = context.user_data.get('quiz_index', 0)
    questions = context.user_data.get('quiz_queue', [])
    total = context.user_data.get('quiz_total', 0)

    if index >= total or index >= len(questions):
        correct = context.user_data.get('quiz_correct', 0)
        total_q = context.user_data.get('quiz_total', 0)
        score = (correct / total_q * 100) if total_q > 0 else 0

        await context.bot.send_message(
            chat_id=chat_id,
            text=f"🏁 <b>انتهى الاختبار!</b>\n\n"
                 f"✅ {correct}/{total_q} صحيحة\n"
                 f"📊 النسبة: {score:.1f}%\n"
                 f"🏆 النقاط: {correct * 10}\n\n"
                 f"📝 استخدم /quiz لبدء جلسة جديدة.",
            parse_mode="HTML"
        )
        context.user_data.pop('quiz_queue', None)
        context.user_data.pop('quiz_index', None)
        context.user_data.pop('quiz_correct', None)
        context.user_data.pop('quiz_total', None)
        return

    question_data = questions[index]
    progress_bar = "█" * int((index / total) * 20) + "░" * (20 - int((index / total) * 20))
    progress_text = f"📊 التقدم: {progress_bar} {index}/{total}"

    keyboard = [
        [InlineKeyboardButton("🔵 A", callback_data=f"quiz_A_{index}"),
         InlineKeyboardButton("🟢 B", callback_data=f"quiz_B_{index}")],
        [InlineKeyboardButton("🟡 C", callback_data=f"quiz_C_{index}"),
         InlineKeyboardButton("🔴 D", callback_data=f"quiz_D_{index}")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    sent_msg = await context.bot.send_message(
        chat_id=chat_id,
        text=f"⏳ <b>السؤال {index+1} من {total}</b>\n"
             f"{progress_text}\n\n"
             f"{question_data['question']}\n\n"
             f"🅰️ {question_data['option_a']}\n"
             f"🅱️ {question_data['option_b']}\n"
             f"🅲️ {question_data['option_c']}\n"
             f"🅳️ {question_data['option_d']}",
        parse_mode="HTML",
        reply_markup=reply_markup
    )

    loop = asyncio.get_event_loop()
    timer_job = loop.call_later(60, lambda: asyncio.create_task(handle_timeout(context, chat_id, index, sent_msg.message_id)))
    context.user_data['quiz_timer_job'] = timer_job

async def handle_timeout(context: ContextTypes.DEFAULT_TYPE, chat_id: int, index: int, message_id: int):
    if context.user_data.get('quiz_index') != index:
        return

    questions = context.user_data.get('quiz_queue', [])
    if index >= len(questions):
        return

    question_data = questions[index]
    correct_answer = question_data['correct_answer']

    await context.bot.edit_message_text(
        chat_id=chat_id,
        message_id=message_id,
        text=f"⏰ <b>انتهى الوقت!</b>\n\n"
             f"السؤال: {question_data['question']}\n"
             f"✅ الإجابة الصحيحة: <b>{correct_answer}</b>\n\n"
             f"📖 {question_data.get('explanation', '')}\n\n"
             f"⏳ جاري الانتقال إلى السؤال التالي...",
        parse_mode="HTML",
        reply_markup=None
    )

    context.user_data['quiz_index'] = index + 1
    await asyncio.sleep(2)
    await send_question_from_context(context, chat_id)

async def send_question_from_context(context: ContextTypes.DEFAULT_TYPE, chat_id: int):
    index = context.user_data.get('quiz_index', 0)
    questions = context.user_data.get('quiz_queue', [])
    total = context.user_data.get('quiz_total', 0)

    if index >= total or index >= len(questions):
        correct = context.user_data.get('quiz_correct', 0)
        total_q = context.user_data.get('quiz_total', 0)
        score = (correct / total_q * 100) if total_q > 0 else 0

        await context.bot.send_message(
            chat_id=chat_id,
            text=f"🏁 <b>انتهى الاختبار!</b>\n\n"
                 f"✅ {correct}/{total_q} صحيحة\n"
                 f"📊 النسبة: {score:.1f}%\n"
                 f"🏆 النقاط: {correct * 10}\n\n"
                 f"📝 استخدم /quiz لبدء جلسة جديدة.",
            parse_mode="HTML"
        )
        context.user_data.pop('quiz_queue', None)
        context.user_data.pop('quiz_index', None)
        context.user_data.pop('quiz_correct', None)
        context.user_data.pop('quiz_total', None)
        return

    question_data = questions[index]
    progress_bar = "█" * int((index / total) * 20) + "░" * (20 - int((index / total) * 20))
    progress_text = f"📊 التقدم: {progress_bar} {index}/{total}"

    keyboard = [
        [InlineKeyboardButton("🔵 A", callback_data=f"quiz_A_{index}"),
         InlineKeyboardButton("🟢 B", callback_data=f"quiz_B_{index}")],
        [InlineKeyboardButton("🟡 C", callback_data=f"quiz_C_{index}"),
         InlineKeyboardButton("🔴 D", callback_data=f"quiz_D_{index}")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    sent_msg = await context.bot.send_message(
        chat_id=chat_id,
        text=f"⏳ <b>السؤال {index+1} من {total}</b>\n"
             f"{progress_text}\n\n"
             f"{question_data['question']}\n\n"
             f"🅰️ {question_data['option_a']}\n"
             f"🅱️ {question_data['option_b']}\n"
             f"🅲️ {question_data['option_c']}\n"
             f"🅳️ {question_data['option_d']}",
        parse_mode="HTML",
        reply_markup=reply_markup
    )

    loop = asyncio.get_event_loop()
    timer_job = loop.call_later(60, lambda: asyncio.create_task(handle_timeout(context, chat_id, index, sent_msg.message_id)))
    context.user_data['quiz_timer_job'] = timer_job

async def handle_quiz_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = query.from_user
    user_id = user.id
    data = query.data

    if not data.startswith("quiz_"):
        return

    parts = data.split("_")
    if len(parts) < 3:
        return

    user_answer = parts[1]
    try:
        index = int(parts[2])
    except ValueError:
        await query.edit_message_text("⚠️ حدث خطأ، حاول مرة أخرى.")
        return

    timer_job = context.user_data.get('quiz_timer_job')
    if timer_job:
        timer_job.cancel()
        context.user_data['quiz_timer_job'] = None

    questions = context.user_data.get('quiz_queue', [])
    if index >= len(questions):
        await query.edit_message_text("⚠️ حدث خطأ، حاول بدء جلسة جديدة بـ /quiz.")
        return

    question_data = questions[index]
    correct = question_data['correct_answer']
    is_correct = (user_answer == correct)

    if is_correct:
        update_user_stats(user_id, True, 10)
        context.user_data['quiz_correct'] = context.user_data.get('quiz_correct', 0) + 1

    save_answer_history(user_id, question_data['id'], user_answer, is_correct)

    context.user_data['quiz_index'] = index + 1

    await query.edit_message_text(
        f"{'✅ صحيح! 🎉' if is_correct else f'❌ خطأ! الإجابة الصحيحة هي {correct}'}\n\n"
        f"📖 {question_data.get('explanation', '')}\n\n"
        f"📊 التقدم: {context.user_data['quiz_index']}/{context.user_data['quiz_total']}\n"
        f"🏆 النقاط: {context.user_data.get('quiz_correct', 0) * 10}",
        parse_mode="HTML"
    )

    await asyncio.sleep(1.5)
    await send_question_from_context(context, query.message.chat_id)

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = get_leaderboard(10)
    if not data:
        await update.message.reply_text(
            "🏆 <b>لا يوجد لاعبون مسجلون بعد!</b>\n\n"
            "📝 كن أول من يبدأ الاختبار بـ /quiz",
            parse_mode="HTML"
        )
        return

    text = "🏆 <b>لوحة المتصدرين</b>\n━━━━━━━━━━━━━━━━━━━━━\n\n"
    medals = ["🥇", "🥈", "🥉"]
    for idx, user in enumerate(data):
        medal = medals[idx] if idx < 3 else f"{idx+1}."
        name = user.get("first_name", f"ID:{user['user_id']}")
        points = user.get("total_points", 0)
        correct = user.get("correct_answers", 0)
        text += f"{medal} {name} - {points} نقطة ✅\n"

    text += "\n━━━━━━━━━━━━━━━━━━━━━\n"
    text += "📌 <i>تحديث فوري مع كل إجابة</i>"
    await update.message.reply_text(text, parse_mode="HTML")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    user_data = get_user(user_id)
    if not user_data:
        await update.message.reply_text(
            "❌ <b>لا توجد بيانات لك!</b>\n\n"
            "📝 ابدأ الاختبار بـ /quiz",
            parse_mode="HTML"
        )
        return

    correct = user_data.get("correct_answers", 0)
    wrong = user_data.get("wrong_answers", 0)
    points = user_data.get("total_points", 0)
    total = correct + wrong
    success_rate = (correct / total * 100) if total > 0 else 0

    if points <= 50: level, emoji = "📗 مبتدئ", "🌱"
    elif points <= 100: level, emoji = "📘 متعلم", "📚"
    elif points <= 200: level, emoji = "📙 خبير", "🧠"
    else: level, emoji = "🏅 أسطورة", "👑"

    await update.message.reply_text(
        f"📊 <b>إحصائياتك</b>\n━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>{user_data.get('first_name', 'مستخدم')}</b>\n"
        f"{emoji} <b>{level}</b>\n\n"
        f"🏆 <b>النقاط:</b> {points}\n"
        f"✅ <b>الإجابات الصحيحة:</b> {correct}\n"
        f"❌ <b>الإجابات الخاطئة:</b> {wrong}\n"
        f"📊 <b>الإجمالي:</b> {total}\n"
        f"📈 <b>نسبة النجاح:</b> {success_rate:.1f}%\n"
        f"📅 <b>آخر إجابة:</b> {user_data.get('last_answered', 'لم يجب بعد')}\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"📌 <i>استمر في التحدي!</i>",
        parse_mode="HTML"
    )

# ===================== تسجيل المجموعة عند إضافة البوت =====================

async def handle_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عند إضافة البوت إلى مجموعة جديدة، يتم تسجيلها"""
    for new_member in update.message.new_chat_members:
        if new_member.id == context.bot.id:
            chat_id = update.effective_chat.id
            register_group(chat_id)
            await update.message.reply_text(
                "🧠 تم تفعيل Pi Quiz في هذه المجموعة!\n"
                "سيتم إرسال أسئلة يومية (20-50 سؤال) في الساعة 10 صباحاً.\n"
                "يمكنك أيضاً استخدام /quiz لبدء اختبار خاص."
            )
            break

# ===================== تشغيل البوت =====================

def main():
    initialize_questions()

    app = Application.builder().token(TOKEN).build()

    # الأوامر الأساسية
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help))
    app.add_handler(CommandHandler("quiz", quiz))
    app.add_handler(CommandHandler("leaderboard", leaderboard))
    app.add_handler(CommandHandler("stats", stats))

    # معالج إضافة البوت إلى المجموعات
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, handle_new_member))

    # معالج الأزرار (للأسئلة اليومية والأسئلة العادية)
    app.add_handler(CallbackQueryHandler(handle_quiz_answer, pattern="^quiz_"))
    app.add_handler(CallbackQueryHandler(handle_daily_answer, pattern="^daily_"))

    # الجدولة
    scheduler = AsyncIOScheduler()

    # إرسال الأسئلة اليومية في الساعة 10:00 صباحاً
    scheduler.add_job(
        send_daily_questions,
        CronTrigger(hour=SEND_HOUR, minute=SEND_MINUTE),
        args=[app]
    )
    print(f"📅 تم جدولة الأسئلة اليومية (الساعة {SEND_HOUR}:{SEND_MINUTE:02d})")

    scheduler.start()

    print("🧠 Pi Quiz Bot يعمل مع الإرسال اليومي التلقائي...")
    app.run_polling()


if __name__ == "__main__":
    main()
