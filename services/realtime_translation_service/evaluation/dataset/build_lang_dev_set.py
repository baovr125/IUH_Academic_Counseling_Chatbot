# -*- coding: utf-8 -*-
"""Dựng bộ dev/val để HIỆU CHỈNH Language Detection (không phải bộ test chính thức).

Bộ test của evaluation.md phải được dựng riêng từ nguồn khác và đóng băng; file này chỉ phục vụ
tinh chỉnh ngưỡng/meta-confidence và dev-gate. Mọi file ghi ra đều là UTF-8 (không BOM).

Chạy:  python evaluation/dataset/build_lang_dev_set.py
Sinh:  evaluation/dataset/lang_dev.jsonl (~70%) và lang_val.jsonl (~30%), chia cố định theo hash id.
"""
import hashlib
import json
import os
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))

# (category, lang, text) — expected_status=detected, không cho phép abstain.
LONG = {
    "en": [
        "The university announced that registration for the spring semester will open next Monday.",
        "Machine learning models require large amounts of high quality data to perform well.",
        "She has been working at the hospital for more than ten years and loves her job.",
        "Please make sure that you submit your assignment before the deadline on Friday evening.",
        "The weather forecast says it will rain heavily throughout the weekend in the northern region.",
        "Climate change is one of the most serious challenges that our generation has to face.",
        "He opened the window and listened to the sound of the rain falling on the old roof.",
        "Students are required to complete all prerequisite courses before registering for the thesis.",
        "Our team is developing a real time translation service that supports ten different languages.",
        "I would like to book a table for four people at seven o'clock tonight.",
        "The new library offers quiet study rooms, free internet access and a small cafe on the ground floor.",
        "Scientists have discovered a new species of frog living deep inside the rainforest.",
    ],
    "de": [
        "Die Universität hat angekündigt, dass die Anmeldung für das Sommersemester nächste Woche beginnt.",
        "Ich habe gestern einen langen Spaziergang im Park gemacht und mich sehr gut erholt.",
        "Maschinelles Lernen benötigt große Mengen an qualitativ hochwertigen Daten, um gut zu funktionieren.",
        "Könnten Sie mir bitte sagen, wie ich am schnellsten zum Hauptbahnhof komme?",
        "Der Klimawandel ist eine der größten Herausforderungen unserer Zeit für die ganze Menschheit.",
        "Meine Schwester wohnt seit drei Jahren in Berlin und arbeitet dort als Ingenieurin.",
        "Am Wochenende wollen wir mit der ganzen Familie in die Berge fahren und wandern.",
        "Die Studenten müssen alle Pflichtkurse abschließen, bevor sie ihre Abschlussarbeit anmelden dürfen.",
        "Wir entwickeln einen Übersetzungsdienst in Echtzeit, der zehn verschiedene Sprachen unterstützt.",
        "Es regnet seit dem frühen Morgen und die Straßen sind völlig überflutet.",
        "Das neue Restaurant in der Altstadt bietet frische regionale Gerichte zu fairen Preisen an.",
        "Er hat das Fenster geöffnet und dem Regen zugehört, der auf das alte Dach fiel.",
    ],
    "fr": [
        "L'université a annoncé que les inscriptions pour le semestre de printemps commenceront lundi prochain.",
        "J'ai passé tout l'après-midi à la bibliothèque pour préparer mon examen de demain.",
        "L'apprentissage automatique nécessite de grandes quantités de données de qualité pour bien fonctionner.",
        "Pourriez-vous m'indiquer le chemin le plus rapide pour aller à la gare centrale ?",
        "Le changement climatique est l'un des plus grands défis auxquels notre génération doit faire face.",
        "Ma sœur habite à Lyon depuis trois ans et travaille comme ingénieure dans une grande entreprise.",
        "Ce week-end, nous allons faire une randonnée en montagne avec toute la famille.",
        "Les étudiants doivent valider tous les cours obligatoires avant de s'inscrire au mémoire.",
        "Notre équipe développe un service de traduction en temps réel qui prend en charge dix langues.",
        "Il pleut depuis ce matin et les rues sont complètement inondées dans le centre-ville.",
        "Le nouveau restaurant de la vieille ville propose des plats régionaux frais à des prix raisonnables.",
        "Il a ouvert la fenêtre et écouté la pluie qui tombait sur le vieux toit.",
    ],
    "es": [
        "La universidad anunció que la matrícula para el semestre de primavera comenzará el próximo lunes.",
        "Ayer di un largo paseo por el parque y me sentí mucho mejor después de descansar.",
        "El aprendizaje automático necesita grandes cantidades de datos de calidad para funcionar bien.",
        "¿Podría decirme cuál es el camino más rápido para llegar a la estación central?",
        "El cambio climático es uno de los mayores desafíos que enfrenta nuestra generación.",
        "Mi hermana vive en Madrid desde hace tres años y trabaja como ingeniera en una empresa grande.",
        "Este fin de semana vamos a subir a la montaña con toda la familia.",
        "Los estudiantes deben completar todos los cursos obligatorios antes de inscribir su tesis.",
        "Nuestro equipo desarrolla un servicio de traducción en tiempo real que admite diez idiomas.",
        "Llueve desde la mañana y las calles del centro están completamente inundadas.",
        "El nuevo restaurante del casco antiguo ofrece platos regionales frescos a precios razonables.",
        "Abrió la ventana y escuchó la lluvia que caía sobre el viejo tejado.",
    ],
    "ru": [
        "Университет объявил, что регистрация на весенний семестр начнётся в следующий понедельник.",
        "Вчера я долго гулял по парку и почувствовал себя намного лучше после отдыха.",
        "Машинному обучению требуется большое количество качественных данных для хорошей работы.",
        "Не могли бы вы подсказать, как быстрее всего добраться до главного вокзала?",
        "Изменение климата — одна из самых серьёзных проблем, с которыми сталкивается наше поколение.",
        "Моя сестра живёт в Москве уже три года и работает инженером в большой компании.",
        "В выходные мы поедем с семьёй в горы и пойдём в поход.",
        "Студенты должны сдать все обязательные курсы перед тем, как подать заявку на диплом.",
        "Наша команда разрабатывает сервис перевода в реальном времени, поддерживающий десять языков.",
        "С самого утра идёт дождь, и улицы в центре города полностью затоплены.",
        "Новый ресторан в старом городе предлагает свежие блюда местной кухни по разумным ценам.",
        "Он открыл окно и слушал, как дождь стучит по старой крыше.",
    ],
    "vi": [
        "Trường đại học thông báo rằng đăng ký học kỳ mùa xuân sẽ mở vào thứ Hai tuần sau.",
        "Hôm qua tôi đã đi dạo rất lâu trong công viên và cảm thấy khỏe hơn nhiều.",
        "Các mô hình học máy cần một lượng lớn dữ liệu chất lượng cao để hoạt động hiệu quả.",
        "Bạn có thể cho tôi biết đường nhanh nhất để đến ga trung tâm không?",
        "Biến đổi khí hậu là một trong những thách thức lớn nhất mà thế hệ chúng ta phải đối mặt.",
        "Chị gái tôi sống ở Hà Nội đã ba năm và làm kỹ sư cho một công ty lớn.",
        "Cuối tuần này cả gia đình chúng tôi sẽ lên núi đi bộ đường dài.",
        "Sinh viên phải hoàn thành tất cả các môn bắt buộc trước khi đăng ký làm khóa luận.",
        "Nhóm chúng tôi đang phát triển dịch vụ dịch thuật thời gian thực hỗ trợ mười ngôn ngữ.",
        "Trời mưa từ sáng sớm và nhiều con đường ở trung tâm thành phố bị ngập hoàn toàn.",
        "Nhà hàng mới ở khu phố cổ phục vụ các món ăn địa phương tươi ngon với giá hợp lý.",
        "Anh ấy mở cửa sổ và lắng nghe tiếng mưa rơi trên mái nhà cũ.",
    ],
    "zh": [
        "大学宣布春季学期的注册将于下周一开始。",
        "昨天我在公园里散了很长时间的步，休息之后感觉好多了。",
        "机器学习模型需要大量高质量的数据才能表现良好。",
        "请问去中央火车站最快的路怎么走？",
        "气候变化是我们这一代人面临的最严峻的挑战之一。",
        "我姐姐在北京住了三年，在一家大公司当工程师。",
        "这个周末我们全家打算去山里徒步旅行。",
        "学生必须修完所有必修课程才能申请毕业论文。",
        "我们团队正在开发一项支持十种语言的实时翻译服务。",
        "从早上起就一直在下雨，市中心的街道已经完全被淹了。",
        "老城区新开的餐厅以合理的价格提供新鲜的地方菜肴。",
        "他打开窗户，静静地听着雨点落在旧屋顶上的声音。",
    ],
    "ja": [
        "大学は春学期の履修登録が来週の月曜日に始まると発表しました。",
        "昨日は公園で長い時間散歩をして、休んだ後とても気分が良くなりました。",
        "機械学習モデルがうまく機能するには、大量の高品質なデータが必要です。",
        "中央駅へ行く一番早い道を教えていただけませんか。",
        "気候変動は私たちの世代が直面している最も深刻な課題の一つです。",
        "姉は東京に三年間住んでいて、大きな会社でエンジニアとして働いています。",
        "今週末は家族みんなで山へハイキングに行く予定です。",
        "学生は卒業論文を申請する前に、すべての必修科目を修了しなければなりません。",
        "私たちのチームは十の言語に対応したリアルタイム翻訳サービスを開発しています。",
        "朝から雨が降り続いていて、市内の道路は完全に冠水しています。",
        "旧市街の新しいレストランは、新鮮な郷土料理を手頃な価格で提供しています。",
        "彼は窓を開けて、古い屋根に降る雨の音に耳を澄ませました。",
    ],
    "ko": [
        "대학은 봄 학기 수강 신청이 다음 주 월요일에 시작된다고 발표했습니다.",
        "어제 공원에서 오랫동안 산책을 했더니 기분이 훨씬 좋아졌습니다.",
        "기계 학습 모델이 잘 작동하려면 많은 양의 고품질 데이터가 필요합니다.",
        "중앙역까지 가장 빨리 가는 길을 알려 주시겠어요?",
        "기후 변화는 우리 세대가 직면한 가장 심각한 도전 중 하나입니다.",
        "제 누나는 서울에서 삼 년째 살면서 큰 회사에서 엔지니어로 일하고 있습니다.",
        "이번 주말에는 온 가족이 산으로 하이킹을 갈 계획입니다.",
        "학생들은 졸업 논문을 신청하기 전에 모든 필수 과목을 이수해야 합니다.",
        "저희 팀은 열 개 언어를 지원하는 실시간 번역 서비스를 개발하고 있습니다.",
        "아침부터 비가 계속 내려서 시내 도로가 완전히 물에 잠겼습니다.",
        "구시가지에 새로 문을 연 식당은 신선한 향토 요리를 합리적인 가격에 제공합니다.",
        "그는 창문을 열고 낡은 지붕 위로 떨어지는 빗소리에 귀를 기울였습니다.",
    ],
    "th": [
        "มหาวิทยาลัยประกาศว่าการลงทะเบียนเรียนภาคเรียนฤดูใบไม้ผลิจะเริ่มในวันจันทร์หน้า",
        "เมื่อวานฉันเดินเล่นในสวนสาธารณะนานมากและรู้สึกดีขึ้นมากหลังจากได้พักผ่อน",
        "โมเดลการเรียนรู้ของเครื่องต้องใช้ข้อมูลคุณภาพสูงจำนวนมากจึงจะทำงานได้ดี",
        "ช่วยบอกทางที่เร็วที่สุดไปสถานีรถไฟกลางได้ไหมคะ",
        "การเปลี่ยนแปลงสภาพภูมิอากาศเป็นหนึ่งในความท้าทายที่ร้ายแรงที่สุดของคนรุ่นเรา",
        "พี่สาวของฉันอาศัยอยู่ที่กรุงเทพมาสามปีแล้วและทำงานเป็นวิศวกรในบริษัทใหญ่",
        "สุดสัปดาห์นี้ครอบครัวของเราจะไปเดินป่าบนภูเขาด้วยกัน",
        "นักศึกษาต้องเรียนวิชาบังคับทั้งหมดให้ครบก่อนจึงจะลงทะเบียนทำวิทยานิพนธ์ได้",
        "ทีมของเรากำลังพัฒนาบริการแปลภาษาแบบเรียลไทม์ที่รองรับสิบภาษา",
        "ฝนตกตั้งแต่เช้าและถนนในใจกลางเมืองถูกน้ำท่วมทั้งหมด",
        "ร้านอาหารใหม่ในเมืองเก่าเสิร์ฟอาหารท้องถิ่นสดใหม่ในราคาที่เหมาะสม",
        "เขาเปิดหน้าต่างและฟังเสียงฝนที่ตกลงบนหลังคาเก่า",
    ],
}

# Câu 3–5 từ: kỳ vọng `detected`, nhưng cho phép abstain (abstain_ok).
MEDIUM = {
    "en": ["Where is the station?", "Thank you very much", "See you tomorrow morning", "I am very tired", "What time is it"],
    "de": ["Wo ist der Bahnhof?", "Vielen Dank für alles", "Bis morgen früh", "Ich bin sehr müde", "Wie spät ist es"],
    "fr": ["Où est la gare ?", "Merci beaucoup pour tout", "À demain matin", "Je suis très fatigué", "Quelle heure est-il"],
    "es": ["¿Dónde está la estación?", "Muchas gracias por todo", "Hasta mañana por la mañana", "Estoy muy cansado", "¿Qué hora es?"],
    "ru": ["Где находится вокзал?", "Большое спасибо за всё", "До завтра утром", "Я очень устал", "Который сейчас час?"],
    "vi": ["Nhà ga ở đâu vậy?", "Cảm ơn bạn rất nhiều", "Hẹn gặp lại sáng mai", "Tôi rất mệt", "Mấy giờ rồi nhỉ?"],
    "zh": ["火车站在哪里？", "非常感谢你", "明天早上见", "我很累", "现在几点了？"],
    "ja": ["駅はどこですか。", "本当にありがとうございます", "また明日の朝に会いましょう", "とても疲れました", "今何時ですか。"],
    "ko": ["역이 어디예요?", "정말 감사합니다", "내일 아침에 봐요", "저는 너무 피곤해요", "지금 몇 시예요?"],
    "th": ["สถานีอยู่ที่ไหน", "ขอบคุณมากสำหรับทุกอย่าง", "เจอกันพรุ่งนี้เช้า", "ฉันเหนื่อยมาก", "ตอนนี้กี่โมงแล้ว"],
}

# 1–2 từ: abstain_ok.
SHORT = {
    "en": ["Hello", "Thanks", "Good morning", "Yes please", "computer", "Okay then"],
    "de": ["Danke", "Guten Morgen", "Hallo zusammen", "Entschuldigung"],
    "fr": ["Merci", "Bonjour", "Au revoir", "S'il vous plaît"],
    "es": ["Gracias", "Buenos días", "Hola amigos", "Por favor"],
    "ru": ["Привет", "Спасибо", "Здравствуйте"],
    "vi": ["Xin chào", "Cảm ơn", "Tạm biệt", "Xin lỗi"],
    "zh": ["你好", "谢谢", "再见", "对不起"],
    "ja": ["ありがとう", "こんにちは", "さようなら"],
    "ko": ["안녕하세요", "감사합니다", "안녕"],
    "th": ["สวัสดี", "ขอบคุณ", "ลาก่อน"],
}

VI_NO_ACCENT = [
    "toi dang hoc lap trinh tai truong dai hoc cong nghiep",
    "ban co the giup toi kiem tra bai khong",
    "hom qua thay giao tra bai kiem tra cho chung toi",
    "sinh vien can nop bai tap truoc ky thi giua ky",
    "ngay mai troi se mua to nen chung ta o nha thoi",
    "toi muon dat ban cho bon nguoi vao luc bay gio toi nay",
    "cam on ban da giup do toi rat nhieu trong tuan qua",
    "thu vien moi co phong doc yen tinh va quan ca phe nho",
    "chung toi dang phat trien dich vu dich thuat thoi gian thuc",
    "em khong hieu bai nay thay oi giai thich lai giup em voi",
    "cuoi tuan nay ca gia dinh toi se di leo nui",
    "anh co biet duong den nha ga trung tam khong",
    "mon hoc nay kho qua nhung giao vien day rat hay",
    "toi se gui email cho thay vao sang mai",
    "gia xang tang lien tuc lam nhieu nguoi lo lang",
    "ke hoach hoc tap hoc ky nay cua em nhu the nao",
    "cong ty cua chung toi dang tuyen nhieu ky su moi",
    "nho nop hoc phi truoc ngay muoi lam nhe",
    "trong thu vien khong duoc noi chuyen to",
    "chung ta can phat trien tri tue nhan tao mot cach an toan",
]
VI_NO_ACCENT_SHORT = ["xin chao", "cam on", "tam biet", "xin loi"]

VI_WRONG_DIACRITIC = [
    "Tri tuệ nhân tao đang thay đôi giáo duc nhanh chong",
    "Hom nay trời đep quá chúng ta đi choi nhe",
    "Bạn co thể giúp tôi dich đoạn van nay không",
    "Sinh vien phai nộp bai truoc thứ sáu",
    "Tôi rất thích học tiếng Anh nhưng phát âm con yếu",
    "Thây giáo vưa giao bai tập về nhà rât nhiều",
    "Mình dang tim phong tro gân trương dai hoc",
    "Cam on ban đa chia sẻ tai liệu huu ích nay",
]

VI_TEENCODE = [
    "hok hiểu sao môn này khó vậy nek",
    "oke bạn ơi tui học khum vô lớp được",
    "ko bik lm sao luon á",
    "mn oi cho minh hoi bai nay lam sao",
    "j vậy trời sao ko ai rep tn",
    "hnay dc nghỉ hok mn",
    "bn oi giup tui voi",
    "tui dang on thi nè",
    "cj oi cho em hoi chut",
    "nay đi hok z mn",
]

VI_EN_MIXED = [
    "Hôm nay tôi có meeting với team về deadline quan trọng",
    "Bạn đã review pull request chưa tôi cần merge trước deadline",
    "Em cần submit assignment trước 11pm được không ạ",
    "Tôi vừa deploy xong ứng dụng lên server",
    "Chúng ta cần optimize database để giảm latency",
    "Thầy ơi em muốn xin feedback về bài thesis của em",
    "Cuối tuần này mình đi hiking ở Đà Lạt nhé",
    "Dự án này cần thêm một developer có kinh nghiệm về backend",
    "Anh gửi giúp em file báo cáo qua email nhé",
    "Hôm nay tôi học machine learning và deep learning",
]

EN_SLANG = [
    "lol that exam was so hard idk how i passed tbh",
    "omg did u see the new update yet",
    "gonna finish this homework asap lol",
    "brb gotta grab some coffee real quick",
    "thx for the help guys really appreciate it",
    "idk what to do anymore honestly",
    "u free tonight we should hang out",
    "btw the meeting got moved to friday",
    "imo this approach is way better than the old one",
    "gtg talk to you later bye",
]
EN_TYPO = [
    "I thnk this machin learing is intersting",
    "Pleese send me the documnet tomorow morning",
    "She dont know where is the libary",
    "teh server is runing slowley today",
    "I recieved you're message yesterday evening",
]
OTHER_TYPO = [
    ("de", "Ich habe gestren eine neuen Computer gekauft und er funktioniert sher gut"),
    ("fr", "Je ne sais pa comment faire sa sans votre aide aujourd'hui"),
    ("es", "Ayer fui al sine con mis amigos y nos divertimos mucho"),
]

# Bẫy marker: câu tiếng Anh chứa token trùng marker de/fr/es.
EN_MARKER_TRAPS = [
    "the die is cast and there is no turning back now",
    "my son is here to see the doctor this afternoon",
    "please put the empty bottles in the recycling bin outside",
    "the lion returned to its den after hunting all night",
    "it was just a con to steal money from old people",
    "he scored par on the last hole and won the tournament",
    "I like pizza plus a large glass of cold water",
    "she will die laughing when she hears this funny story",
    "the son and daughter helped their father in the garden",
    "do not throw that into the bin because it is still useful",
    "the dog dug a den under the fence behind our house",
    "a con artist tricked the whole village last summer",
]

# Ngôn ngữ ngoài phạm vi (kỳ vọng unsupported; nếu detected → false-accept).
OOS = {
    "it": [
        "L'università ha annunciato che le iscrizioni per il semestre primaverile inizieranno lunedì prossimo.",
        "Ieri ho fatto una lunga passeggiata nel parco e mi sono sentito molto meglio.",
        "Potrebbe dirmi qual è la strada più veloce per arrivare alla stazione centrale?",
        "Il cambiamento climatico è una delle sfide più gravi che la nostra generazione deve affrontare.",
        "Mia sorella vive a Roma da tre anni e lavora come ingegnere in una grande azienda.",
        "Il nuovo ristorante nel centro storico offre piatti regionali freschi a prezzi ragionevoli.",
        "La intelligenza artificiale sta cambiando il modo in cui studiamo e lavoriamo ogni giorno.",
        "Questo fine settimana andiamo in montagna con tutta la famiglia per fare una passeggiata.",
    ],
    "pt": [
        "A universidade anunciou que as inscrições para o semestre de primavera começam na próxima segunda-feira.",
        "Ontem dei um longo passeio no parque e me senti muito melhor depois de descansar.",
        "Você poderia me dizer qual é o caminho mais rápido para chegar à estação central?",
        "A mudança climática é um dos maiores desafios que a nossa geração precisa enfrentar.",
        "Minha irmã mora em Lisboa há três anos e trabalha como engenheira numa grande empresa.",
        "O novo restaurante da cidade velha oferece pratos regionais frescos a preços razoáveis.",
        "A inteligência artificial está mudando a forma como estudamos e trabalhamos todos os dias.",
        "Neste fim de semana vamos para a montanha com toda a família fazer uma caminhada.",
    ],
    "id": [
        "Universitas mengumumkan bahwa pendaftaran semester genap akan dibuka pada hari Senin depan.",
        "Kemarin saya berjalan-jalan cukup lama di taman dan merasa jauh lebih baik.",
        "Bisakah Anda memberi tahu jalan tercepat menuju stasiun pusat?",
        "Perubahan iklim adalah salah satu tantangan terbesar yang dihadapi generasi kita.",
        "Kecerdasan buatan sedang mengubah cara kita belajar dan bekerja setiap hari.",
        "Akhir pekan ini kami sekeluarga akan pergi mendaki gunung bersama.",
    ],
    "ms": [
        "Universiti mengumumkan bahawa pendaftaran semester baharu akan dibuka pada hari Isnin depan.",
        "Semalam saya berjalan-jalan agak lama di taman dan berasa jauh lebih baik.",
        "Bolehkah anda beritahu jalan paling pantas ke stesen pusat?",
        "Hujan turun dengan lebat sejak pagi dan banyak jalan di bandar ditenggelami air.",
    ],
    "nl": [
        "De universiteit heeft aangekondigd dat de inschrijving voor het voorjaarssemester volgende week maandag begint.",
        "Gisteren heb ik lang gewandeld in het park en ik voelde me veel beter.",
        "Kunt u mij vertellen wat de snelste weg naar het centraal station is?",
        "Klimaatverandering is een van de grootste uitdagingen waar onze generatie voor staat.",
        "Mijn zus woont al drie jaar in Amsterdam en werkt als ingenieur bij een groot bedrijf.",
        "Het nieuwe restaurant in de oude stad serveert verse regionale gerechten tegen redelijke prijzen.",
    ],
    "pl": [
        "Uniwersytet ogłosił, że zapisy na semestr letni rozpoczną się w przyszły poniedziałek.",
        "Wczoraj długo spacerowałem po parku i poczułem się znacznie lepiej.",
        "Czy może mi pan powiedzieć, jak najszybciej dojść na dworzec główny?",
        "Zmiany klimatyczne są jednym z największych wyzwań, przed którymi stoi nasze pokolenie.",
        "Moja siostra mieszka w Warszawie od trzech lat i pracuje jako inżynier w dużej firmie.",
    ],
    "tr": [
        "Üniversite, bahar dönemi kayıtlarının önümüzdeki pazartesi başlayacağını duyurdu.",
        "Dün parkta uzun bir yürüyüş yaptım ve kendimi çok daha iyi hissettim.",
        "Merkez istasyona giden en hızlı yolu söyleyebilir misiniz?",
        "İklim değişikliği, neslimizin karşı karşıya olduğu en büyük zorluklardan biridir.",
        "Ablam üç yıldır İstanbul'da yaşıyor ve büyük bir şirkette mühendis olarak çalışıyor.",
    ],
    "sv": [
        "Universitetet meddelade att anmälan till vårterminen öppnar nästa måndag.",
        "Igår gick jag en lång promenad i parken och mådde mycket bättre efteråt.",
        "Kan du berätta hur jag tar mig till centralstationen så fort som möjligt?",
        "Min syster har bott i Stockholm i tre år och arbetar som ingenjör på ett stort företag.",
    ],
    "da": [
        "Universitetet har meddelt, at tilmeldingen til forårssemesteret åbner næste mandag.",
        "I går gik jeg en lang tur i parken og følte mig meget bedre bagefter.",
        "Min søster har boet i København i tre år og arbejder som ingeniør i en stor virksomhed.",
    ],
    "ro": [
        "Universitatea a anunțat că înscrierile pentru semestrul de primăvară încep lunea viitoare.",
        "Ieri m-am plimbat mult prin parc și m-am simțit mult mai bine după aceea.",
        "Sora mea locuiește la București de trei ani și lucrează ca inginer într-o companie mare.",
        "Schimbările climatice sunt una dintre cele mai mari provocări ale generației noastre.",
    ],
    "cs": [
        "Univerzita oznámila, že zápis na jarní semestr začne příští pondělí.",
        "Včera jsem se dlouho procházel v parku a cítil jsem se mnohem lépe.",
        "Moje sestra bydlí v Praze už tři roky a pracuje jako inženýrka ve velké firmě.",
    ],
    "hu": [
        "Az egyetem bejelentette, hogy a tavaszi félévre a beiratkozás jövő hétfőn kezdődik.",
        "Tegnap hosszan sétáltam a parkban, és sokkal jobban éreztem magam utána.",
        "A nővérem három éve él Budapesten, és mérnökként dolgozik egy nagy cégnél.",
    ],
    "fi": [
        "Yliopisto ilmoitti, että kevätlukukauden ilmoittautuminen alkaa ensi maanantaina.",
        "Eilen kävelin pitkään puistossa ja tunsin oloni paljon paremmaksi.",
        "Siskoni asuu Helsingissä kolmatta vuotta ja työskentelee insinöörinä isossa yrityksessä.",
    ],
    "hr": [
        "Sveučilište je objavilo da upisi za proljetni semestar počinju sljedeći ponedjeljak.",
        "Jučer sam dugo šetao parkom i nakon toga sam se osjećao puno bolje.",
        "Moja sestra živi u Zagrebu već tri godine i radi kao inženjerka u velikoj tvrtki.",
    ],
    "ca": [
        "La universitat ha anunciat que la matrícula del semestre de primavera començarà dilluns vinent.",
        "Ahir vaig fer una passejada llarga pel parc i em vaig sentir molt millor.",
        "La meva germana viu a Barcelona des de fa tres anys i treballa d'enginyera en una empresa gran.",
    ],
    "no": [
        "Universitetet kunngjorde at påmeldingen til vårsemesteret åpner neste mandag.",
        "I går gikk jeg en lang tur i parken og følte meg mye bedre etterpå.",
        "Søsteren min har bodd i Oslo i tre år og jobber som ingeniør i et stort selskap.",
    ],
    "uk": [
        "Університет оголосив, що реєстрація на весняний семестр розпочнеться наступного понеділка.",
        "Вчора я довго гуляв парком і почувався набагато краще після відпочинку.",
        "Моя сестра живе в Києві вже три роки і працює інженером у великій компанії.",
        "Штучний інтелект змінює спосіб, у який ми вчимося та працюємо щодня.",
    ],
    "bg": [
        "Университетът обяви, че записването за пролетния семестър започва следващия понеделник.",
        "Вчера се разходих дълго в парка и се почувствах много по-добре.",
        "Сестра ми живее в София от три години и работи като инженер във голяма компания.",
    ],
    "ar": [
        "أعلنت الجامعة أن التسجيل للفصل الدراسي الربيعي سيبدأ يوم الاثنين القادم.",
        "أمس مشيت طويلا في الحديقة وشعرت بتحسن كبير بعد ذلك.",
        "الذكاء الاصطناعي يغير الطريقة التي ندرس بها ونعمل كل يوم.",
        "هل يمكنك أن تخبرني بأسرع طريق إلى محطة القطار المركزية؟",
    ],
    "he": [
        "האוניברסיטה הודיעה שההרשמה לסמסטר האביב תתחיל ביום שני הבא.",
        "אתמול טיילתי הרבה זמן בפארק והרגשתי הרבה יותר טוב אחר כך.",
        "אחותי גרה בתל אביב כבר שלוש שנים ועובדת כמהנדסת בחברה גדולה.",
    ],
    "hi": [
        "विश्वविद्यालय ने घोषणा की कि वसंत सत्र के लिए पंजीकरण अगले सोमवार से शुरू होगा।",
        "कल मैं पार्क में बहुत देर तक टहला और उसके बाद मुझे बहुत अच्छा लगा।",
        "मेरी बहन तीन साल से दिल्ली में रहती है और एक बड़ी कंपनी में इंजीनियर है।",
    ],
    "el": [
        "Το πανεπιστήμιο ανακοίνωσε ότι οι εγγραφές για το εαρινό εξάμηνο ξεκινούν την επόμενη Δευτέρα.",
        "Χθες περπάτησα πολλή ώρα στο πάρκο και ένιωσα πολύ καλύτερα μετά.",
        "Η αδελφή μου ζει στην Αθήνα τρία χρόνια και εργάζεται ως μηχανικός σε μεγάλη εταιρεία.",
    ],
    "fa": [
        "دانشگاه اعلام کرد که ثبت نام برای نیمسال بهاری از دوشنبه آینده آغاز می شود.",
        "دیروز مدت زیادی در پارک قدم زدم و بعد از آن احساس بسیار بهتری داشتم.",
    ],
}

NOISE_HTML = [
    ("en", "<p>Machine learning is <b>transforming</b> education around the world</p>"),
    ("vi", "<div><h1>Chào mừng bạn đến với trường đại học công nghiệp</h1></div>"),
    ("de", "<p>Das ist ein <i>sehr</i> wichtiger Hinweis für alle Studenten im ersten Semester</p>"),
    ("fr", "<ul><li>Bonjour tout le monde</li><li>Bienvenue à l'université cette année</li></ul>"),
    ("zh", "<span class='x'>今天天气非常好，我们一起去公园玩吧</span>"),
    ("en", "<script>var x = 1;</script><p>Hello everyone and welcome to the class today</p>"),
    ("es", "<a href=\"https://example.com\">Haga clic aquí para ver más información sobre el curso</a>"),
    ("ru", "<p>Привет всем, добро пожаловать на лекцию по программированию</p>"),
]
NOISE_URL = [
    ("en", "Visit https://www.example.com/docs for the full documentation and many examples"),
    ("vi", "Xem thêm chi tiết tại https://iuh.edu.vn/tuyen-sinh trước ngày mười lăm tháng này"),
    ("de", "Bitte besuchen Sie www.beispiel.de für weitere Informationen zum neuen Kurs"),
    ("en", "Email me at john.doe@example.com if you have any questions about the course"),
    ("es", "Más información en https://ejemplo.es/cursos sobre el nuevo programa de estudios"),
    ("zh", "详情请访问 https://example.cn/news 了解更多关于课程的信息"),
]
INVALID = [
    ("invalid_input", "12345 67890"),
    ("invalid_input", "😊👍🎉🔥"),
    ("invalid_input", "!!! ??? ... ---"),
    ("invalid_input", "    \t  "),
    ("unknown", "https://openai.com/research/gpt4"),
    ("unknown", "john.doe@example.com"),
]
# Code-switching: nhãn chính + cho phép abstain.
CODE_SWITCH = [
    ("vi", "Em cần book vé máy bay cho chuyến đi Đà Nẵng tuần sau"),
    ("vi", "Dự án này có deadline vào thứ Sáu nên cả team phải làm thêm giờ"),
    ("en", "We will meet tomorrow at the quán cà phê near the university"),
    ("vi", "Tôi thích nghe nhạc K-pop mỗi tối sau khi học xong"),
    ("de", "Wir haben heute ein Meeting mit dem ganzen Team um zehn Uhr"),
]


def _nfd(text: str) -> str:
    return unicodedata.normalize("NFD", text)


def build() -> list:
    rows = []

    def add(category, text, lang=None, status="detected", abstain_ok=False, difficulty="easy", note="", group=""):
        rows.append({
            "id": "",
            "group": group,
            "text": text,
            "expected_primary_language": lang,
            "expected_status": status,
            "abstain_ok": abstain_ok,
            "category": category,
            "difficulty": difficulty,
            "notes": note,
        })

    for lang, items in LONG.items():
        for text in items:
            add("standard_long", text, lang)
    for lang, items in MEDIUM.items():
        for text in items:
            add("standard_medium", text, lang, abstain_ok=True, difficulty="medium")
    for lang, items in SHORT.items():
        for text in items:
            add("short", text, lang, abstain_ok=True, difficulty="hard")
    for text in VI_NO_ACCENT:
        add("vietnamese_no_diacritic", text, "vi", abstain_ok=True, difficulty="medium")
    for text in VI_NO_ACCENT_SHORT:
        add("vietnamese_no_diacritic_short", text, "vi", abstain_ok=True, difficulty="hard")
    for text in VI_WRONG_DIACRITIC:
        add("vietnamese_wrong_diacritic", text, "vi", abstain_ok=True, difficulty="medium")
    for text in VI_TEENCODE:
        add("vietnamese_teencode", text, "vi", abstain_ok=True, difficulty="hard")
    for text in VI_EN_MIXED:
        add("code_switching", text, "vi", abstain_ok=True, difficulty="medium")
    for lang, text in CODE_SWITCH:
        add("code_switching", text, lang, abstain_ok=True, difficulty="hard")
    for text in EN_SLANG:
        add("slang_abbreviation", text, "en", difficulty="medium")
    for text in EN_TYPO:
        add("typo", text, "en", abstain_ok=True, difficulty="medium")
    for lang, text in OTHER_TYPO:
        add("typo", text, lang, abstain_ok=True, difficulty="medium")
    for text in EN_MARKER_TRAPS:
        add("marker_trap", text, "en", difficulty="hard")
    for lang, items in OOS.items():
        for text in items:
            add("out_of_scope", text, lang, status="unsupported", difficulty="medium", note="ngôn ngữ ngoài phạm vi")
    for lang, text in NOISE_HTML:
        add("html", text, lang, difficulty="medium")
    for lang, text in NOISE_URL:
        add("url_email", text, lang, difficulty="medium")
    for status, text in INVALID:
        add("invalid_or_non_language", text, None, status=status, difficulty="easy")

    # Mô phỏng gõ dở: tiền tố của câu dài (đúng tình huống realtime). Nhóm theo câu gốc để chia dev/val
    # không rò rỉ giữa các tiền tố của cùng một câu.
    for lang, items in LONG.items():
        for sentence_index in (0, 5, 9):
            sentence = items[sentence_index]
            group = f"prefix_{lang}_{sentence_index}"
            if lang in ("zh", "ja", "ko", "th"):
                lengths = (2, 3, 4, 6, 8)
                prefixes = [sentence[:n] for n in lengths if n < len(sentence)]
            else:
                words = sentence.split()
                prefixes = [" ".join(words[:n]) for n in (1, 2, 3, 4, 5) if n < len(words)]
            for prefix in prefixes:
                add("typing_prefix", prefix, lang, abstain_ok=True, difficulty="hard",
                    note="tiền tố khi đang gõ", group=group)

    # Độ dài/Unicode cực đoan
    add("extreme", " ".join(LONG["en"] * 25)[:3000], "en", note="~3000 ký tự")
    add("extreme", " ".join(LONG["vi"] * 25)[:3000], "vi", note="~3000 ký tự")
    add("extreme", "".join(LONG["zh"] * 25)[:1500], "zh", note="chuỗi Hán dài không dấu cách")
    add("extreme", _nfd(LONG["vi"][1]), "vi", note="Tiếng Việt dạng NFD")
    add("extreme", _nfd(LONG["fr"][2]), "fr", note="Tiếng Pháp dạng NFD")
    add("extreme", "THIS IS A VERY LOUD SENTENCE WRITTEN ENTIRELY IN CAPITAL LETTERS", "en")
    add("extreme", "in 2024 there were 1,500 students and 40 teachers at the faculty of engineering", "en")
    add("extreme", "Hôm nay trời đẹp 😊 chúng ta đi chơi nhé 🎉", "vi")
    add("extreme", "a", None, status="uncertain", abstain_ok=True, difficulty="hard", note="1 ký tự")
    add("extreme", "aaaaaaaaaaaaaaaa", None, status="uncertain", abstain_ok=True, difficulty="hard")
    add("extreme", "Das ist\nein Test\nüber mehrere\nZeilen hinweg geschrieben", "de")

    for index, row in enumerate(rows):
        row["id"] = f"dev_{index:04d}"
    return rows


def split(rows):
    dev, val = [], []
    for row in rows:
        key = row.get("group") or row["id"]
        bucket = int(hashlib.sha1(key.encode()).hexdigest(), 16) % 10
        (dev if bucket < 7 else val).append(row)
    return dev, val


def main():
    rows = build()
    dev, val = split(rows)
    for name, subset in (("lang_dev.jsonl", dev), ("lang_val.jsonl", val)):
        path = os.path.join(HERE, name)
        with open(path, "w", encoding="utf-8", newline="\n") as handle:
            for row in subset:
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")
        print(f"{name}: {len(subset)} mẫu")
    print(f"Tổng: {len(rows)}")


if __name__ == "__main__":
    main()
