"""Dựng bộ dev/val cho Domain Detection (EN->VI), tách khỏi bộ test đóng băng của evaluation.md.

Nguyên tắc:
- dev: dùng để chỉnh quy tắc/ngưỡng; val: chỉ dùng để kiểm tra lại, không chỉnh theo val.
- Mỗi domain có cả câu CÓ thuật ngữ từ điển và câu KHÔNG có (để không thiên vị lexical).
- kind: in_domain | ood (ngoài domain, nhãn unknown) | stray (thuật ngữ từ điển xuất hiện ngoài ngữ cảnh,
  nhãn unknown, báo cáo riêng vì ranh giới mơ hồ) | short (từ/cụm ngắn).
- Chạy:  python evaluation/dataset/build_domain_dev_set.py
"""
import json
import os

IT, MED, ECO, MEC, LAW, MKT = (
    "Công nghệ Thông tin (IT)",
    "Y khoa / Sức khỏe",
    "Kinh tế / Tài chính",
    "Kỹ thuật Cơ khí",
    "Luật / Pháp lý",
    "Marketing",
)
UNK = "unknown"

# (domain, kind, text)
DEV = [
    # ---- IT
    (IT, "in_domain", "After the release, we noticed a memory leak in the worker process, so we profiled the heap and fixed the unclosed connections."),
    (IT, "in_domain", "Using a circuit breaker and rate limiting in front of the payment API prevented the cascading failure during the outage."),
    (IT, "in_domain", "The team decided to pay down technical debt before adding new features to the legacy code."),
    (IT, "in_domain", "Transfer learning lets us start from a pretrained embedding model and fine-tuning it on a small labelled dataset."),
    (IT, "in_domain", "Two threads updated the counter at the same time, producing a race condition that only appeared under heavy load."),
    (IT, "in_domain", "The pull request adds a new REST endpoint and updates the unit tests for the authentication middleware."),
    (IT, "in_domain", "We migrated the monolith to Kubernetes and configured autoscaling for the stateless services."),
    (IT, "in_domain", "SQL injection remains a common vulnerability when user input is concatenated into database queries."),
    (IT, "in_domain", "The compiler reports a type mismatch because the function returns a string instead of an integer."),
    # ---- Y khoa
    (MED, "in_domain", "The clinical trial reported a mild side effect in twelve percent of patients, and no adverse drug reaction required hospitalisation."),
    (MED, "in_domain", "Patients with a history of myocardial infarction and heart failure are at a higher risk factor for readmission."),
    (MED, "in_domain", "Before the study began, every participant gave informed consent and was randomised in a double-blind study."),
    (MED, "in_domain", "The team compared a cohort study with a case-control study to account for a confounding factor."),
    (MED, "in_domain", "Triage nurses assess vital signs first so that patients in respiratory distress are treated immediately."),
    (MED, "in_domain", "The surgeon removed the inflamed appendix laparoscopically and the patient was discharged the next day."),
    (MED, "in_domain", "Metformin is commonly prescribed to lower blood glucose in people with type 2 diabetes."),
    (MED, "in_domain", "A chest X-ray showed pneumonia in the lower lobe of the right lung, so antibiotics were started."),
    (MED, "in_domain", "The vaccine stimulates antibody production and reduces the severity of influenza in older adults."),
    # ---- Kinh tế
    (ECO, "in_domain", "Investors worried about an inverted yield curve as the central bank continued quantitative tightening."),
    (ECO, "in_domain", "A hedge fund and a mutual fund may hold the same stock but differ greatly in fees and strategy."),
    (ECO, "in_domain", "The sunk cost fallacy makes managers continue a failing project because of the opportunity cost they ignore."),
    (ECO, "in_domain", "Free cash flow improved while accounts receivable and working capital stayed under control."),
    (ECO, "in_domain", "The bank's net interest margin narrowed as the credit spread on corporate loans tightened."),
    (ECO, "in_domain", "Rising unemployment and weaker consumer spending pushed the government to cut taxes and raise subsidies."),
    (ECO, "in_domain", "The company reported higher quarterly profit and announced a dividend of fifty cents per share."),
    (ECO, "in_domain", "Exchange rate volatility has made imports more expensive and widened the trade deficit."),
    (ECO, "in_domain", "The portfolio manager rebalanced the assets toward government bonds to reduce risk."),
    # ---- Cơ khí
    (MEC, "in_domain", "Because of stress concentration at the fillet, the shaft showed fatigue failure well below its yield strength."),
    (MEC, "in_domain", "We increased the cutting speed and feed rate, but tool wear and built-up edge reduced the surface roughness quality."),
    (MEC, "in_domain", "An interference fit or a press fit is used when the hub must not slip on the shaft."),
    (MEC, "in_domain", "Heat treatment such as quench hardening improves hardness but may leave residual stress in the heat-affected zone near the weld."),
    (MEC, "in_domain", "The designer applied a factor of safety of two and checked dimensional tolerance with a coordinate measuring machine."),
    (MEC, "in_domain", "The hydraulic cylinder extends when pressurised oil enters the cap end of the piston."),
    (MEC, "in_domain", "A helical gear runs more quietly than a spur gear because the teeth engage gradually."),
    (MEC, "in_domain", "The lathe spindle was aligned and the chuck was tightened before turning the workpiece to the required diameter."),
    (MEC, "in_domain", "A centrifugal pump converts rotational energy from the impeller into kinetic energy of the fluid."),
    # ---- Luật
    (LAW, "in_domain", "The plaintiff failed to meet the burden of proof, so the court applied the presumption of innocence and dismissed the claim."),
    (LAW, "in_domain", "Under the contract, force majeure excuses delay, but a material breach allows the other party to terminate."),
    (LAW, "in_domain", "The statute of limitations had expired before the class action was filed."),
    (LAW, "in_domain", "The court issued a restraining order and later granted an injunction against further trademark infringement."),
    (LAW, "in_domain", "Both parties signed a non-disclosure agreement and a settlement agreement to avoid litigation."),
    (LAW, "in_domain", "The tenant must give written notice to the landlord before terminating the lease agreement."),
    (LAW, "in_domain", "The defendant was convicted of fraud and sentenced to three years in prison."),
    (LAW, "in_domain", "The appeal court overturned the verdict because the judge had admitted unreliable evidence."),
    (LAW, "in_domain", "The company's board adopted a compliance policy to meet new data protection regulations."),
    # ---- Marketing
    (MKT, "in_domain", "To improve the customer journey, we mapped every customer touchpoint and tracked the bounce rate on landing pages."),
    (MKT, "in_domain", "The campaign increased brand awareness, but customer acquisition cost rose as the click-through rate fell."),
    (MKT, "in_domain", "Retargeting and lookalike audience ads improved return on ad spend at the bottom of the funnel."),
    (MKT, "in_domain", "A strong call to action and social proof raised the conversion rate on the product page."),
    (MKT, "in_domain", "Product-market fit comes first; only then should a go-to-market strategy and brand positioning be scaled."),
    (MKT, "in_domain", "The agency designed a new logo and tagline to refresh the company's image among young consumers."),
    (MKT, "in_domain", "We segmented the newsletter list by age and sent personalised offers to loyal shoppers."),
    (MKT, "in_domain", "The influencer posted a short video review that drove thousands of visits to the online store."),
    (MKT, "in_domain", "Market research showed that customers prefer eco-friendly packaging and clear pricing."),
    # ---- Ngoài domain
    (UNK, "ood", "We booked a small hotel near the old town and spent the weekend walking along the river."),
    (UNK, "ood", "Mix the flour, two eggs and a pinch of salt, then let the dough rest for thirty minutes."),
    (UNK, "ood", "The goalkeeper saved a penalty in the last minute and the crowd erupted."),
    (UNK, "ood", "The protagonist of the novel struggles with loneliness after moving to a new city."),
    (UNK, "ood", "It rained all morning, but the sun came out in the afternoon and we went for a walk."),
    (UNK, "ood", "The emperor ordered a great wall to be built along the northern border."),
    (UNK, "ood", "Wild horses galloped across the valley while eagles circled above the cliffs."),
    (UNK, "ood", "The band played an old song and everybody in the café started singing along."),
    (UNK, "ood", "Could you please send me the photos from the birthday party?"),
    (UNK, "ood", "Our teacher asked us to draw a picture of our favourite animal."),
    (UNK, "ood", "She forgot her umbrella on the bus and had to run home in the rain."),
    (UNK, "ood", "The children built a sandcastle and decorated it with shells."),
    (UNK, "ood", "Last summer we visited my cousins in the countryside and helped them harvest rice."),
    (UNK, "ood", "He felt nervous before the interview, but the manager was friendly and relaxed."),
    (UNK, "ood", "The film begins in a quiet village and ends with a dramatic storm at sea."),
    (UNK, "ood", "I usually drink green tea in the morning and read the newspaper on the balcony."),
    # ---- Thuật ngữ lạc ngữ cảnh (ranh giới mơ hồ, báo cáo riêng)
    (UNK, "stray", "Adding too much salt had an unexpected side effect on the sauce, and everyone left the table early."),
    (UNK, "stray", "The bear market stall at the village fair sold honey, bread and wool socks."),
    (UNK, "stray", "Please press fit the cork into the bottle and shake it before serving."),
    (UNK, "stray", "My favourite part of the play was the call to action at the end, when the audience stood up."),
    # ---- Từ/cụm ngắn
    (IT, "short", "memory leak"),
    (MED, "short", "Side effects"),
    (ECO, "short", "yield curve"),
    (MEC, "short", "Heat treatments"),
    (LAW, "short", "burden of proof"),
    (MKT, "short", "the bounce rate"),
    (MEC, "short", "geometric dimensioning and tolerancing"),
    (IT, "short", "technical debts"),
    (MED, "short", "Intensive care unit"),
    (MKT, "short", "retargeting"),
    (UNK, "short", "apple pie"),
    (UNK, "short", "good morning"),
]

VAL = [
    # ---- IT
    (IT, "in_domain", "Our service uses dependency injection and an event loop to handle thousands of concurrent connections."),
    (IT, "in_domain", "The attention mechanism helps the model focus on relevant tokens, but a long context window increases the memory cost."),
    (IT, "in_domain", "<p>Hallucination is a major risk in <b>retrieval-augmented generation</b> when the vector database returns irrelevant passages.</p>"),
    (IT, "in_domain", "The cache invalidation bug only appears after the nightly cron job restarts the container."),
    (IT, "in_domain", "Developers should validate every API request body and hash passwords before storing them in the database."),
    (IT, "in_domain", "The new release switches the build pipeline from Jenkins to GitHub Actions and caches the node modules."),
    # ---- Y khoa
    (MED, "in_domain", "Palliative care focuses on comfort rather than cure for patients with advanced disease."),
    (MED, "in_domain", "Septic shock and multi-organ failure remain the leading causes of death in the intensive care unit."),
    (MED, "in_domain", "The drug interaction between warfarin and the antibiotic increased the bleeding risk, a known adverse event."),
    (MED, "in_domain", "She was diagnosed with iron deficiency anaemia and advised to eat more leafy vegetables and take supplements."),
    (MED, "in_domain", "An electrocardiogram can detect abnormal heart rhythms such as atrial fibrillation."),
    (MED, "in_domain", "Regular exercise lowers blood pressure and reduces the likelihood of developing chronic illness."),
    # ---- Kinh tế
    (ECO, "in_domain", "The central bank's inflation targeting framework failed to prevent stagflation after the oil shock."),
    (ECO, "in_domain", "Venture capital and private equity firms differ in the stage of companies they finance."),
    (ECO, "in_domain", "<div>Auditors questioned <i>revenue recognition</i> and deferred revenue after the company's initial public offering.</div>"),
    (ECO, "in_domain", "A higher interest rate usually reduces borrowing, slows investment and strengthens the currency."),
    (ECO, "in_domain", "The country's gross domestic product grew by two percent while consumer prices remained stable."),
    (ECO, "in_domain", "Many retail investors diversify by buying exchange-traded funds that track a broad stock index."),
    # ---- Cơ khí
    (MEC, "in_domain", "Ultimate tensile strength and fatigue life were measured, and the creep deformation at high temperature was recorded."),
    (MEC, "in_domain", "Excessive backlash and runout in the gear train caused vibration, so the bearing clearance was reduced."),
    (MEC, "in_domain", "Surface finish depends on the depth of cut, tool wear and the chip breaker geometry."),
    (MEC, "in_domain", "The welded bracket was ground smooth and painted to protect it from corrosion."),
    (MEC, "in_domain", "A diesel engine compresses air to a higher ratio than a petrol engine before fuel injection."),
    (MEC, "in_domain", "Torque from the motor is transmitted to the wheels through the gearbox and the differential."),
    # ---- Luật
    (LAW, "in_domain", "The company argued that the contract was frustrated by force majeure and that liquidated damages did not apply."),
    (LAW, "in_domain", "Under due process, the accused has the right to a fair hearing and the presumption of innocence."),
    (LAW, "in_domain", "The beneficial owner of the shares was concealed through shell companies, which raised issues in legal due diligence."),
    (LAW, "in_domain", "The legislature passed a bill that amends the employment code to extend parental leave."),
    (LAW, "in_domain", "The witness testified that she saw the defendant leaving the building shortly before the fire."),
    (LAW, "in_domain", "The lawyer advised her client to sign the lease only after the landlord corrected the clauses on deposits."),
    # ---- Marketing
    (MKT, "in_domain", "Content pillars and lead nurturing helped move a marketing qualified lead into a sales qualified lead."),
    (MKT, "in_domain", "Brand equity grows when share of voice and brand recall rise together."),
    (MKT, "in_domain", "Customer lifetime value should be compared with cost per acquisition before scaling paid media."),
    (MKT, "in_domain", "The launch event combined a livestream, a discount code and a hashtag challenge to attract new followers."),
    (MKT, "in_domain", "She redesigned the packaging to appeal to health-conscious customers and displayed it near the checkout."),
    (MKT, "in_domain", "A/B testing different headlines showed that shorter subject lines made more recipients open the email."),
    # ---- Ngoài domain
    (UNK, "ood", "The train to the coast leaves at eight, so we should pack our bags tonight."),
    (UNK, "ood", "Heat the oil, add the garlic and onions, and stir until they turn golden brown."),
    (UNK, "ood", "The team scored twice in the second half and won the championship for the first time."),
    (UNK, "ood", "In the final chapter, the narrator returns to the village where he was born."),
    (UNK, "ood", "My grandmother told us stories about the war while we watched the rain."),
    (UNK, "ood", "The museum's new exhibition shows paintings from the nineteenth century."),
    (UNK, "ood", "Thank you for your help yesterday; I really appreciate it."),
    (UNK, "ood", "A group of dolphins followed our boat for almost an hour."),
    (UNK, "ood", "The festival begins with a parade and ends with fireworks over the river."),
    (UNK, "ood", "Please remember to water the plants and lock the door before you leave."),
    (UNK, "ood", "The professor asked the students to read two chapters and write a short summary."),
    (UNK, "ood", "He plays the guitar every evening and dreams of recording an album."),
    # ---- Thuật ngữ lạc ngữ cảnh
    (UNK, "stray", "The snowman's melting was a side effect of the warm afternoon, and the kids were disappointed."),
    (UNK, "stray", "The bull market near the harbour sells fresh fish and vegetables every morning."),
    (UNK, "stray", "He used a mallet to press fit the wooden pegs into the toy box."),
    # ---- Từ/cụm ngắn
    (IT, "short", "deadlock"),
    (MED, "short", "Cohort studies"),
    (ECO, "short", "net interest margin"),
    (MEC, "short", "Interference fits"),
    (LAW, "short", "the statute of limitations"),
    (UNK, "short", "good evening"),
]


def _write(rows, name, prefix):
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), name)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for i, (domain, kind, text) in enumerate(rows, 1):
            f.write(json.dumps({"id": f"{prefix}-{i:03d}", "text": text, "domain": domain, "kind": kind}, ensure_ascii=False) + "\n")
    print(f"{name}: {len(rows)} dòng")


if __name__ == "__main__":
    _write(DEV, "domain_dev.jsonl", "dev")
    _write(VAL, "domain_val.jsonl", "val")
