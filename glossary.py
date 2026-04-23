"""不動産業界の用語集。

語句ごとに「原文 → 訳文」のペアで定義する。
翻訳時は __GL_N__ 形式のトークンで該当訳文を保護し、原文中の用語を確実に固定訳にする。
"""

REAL_ESTATE_JA_EN = {
    "専有面積": "Exclusive area",
    "共用部": "Common area",
    "共用部分": "Common area",
    "延床面積": "Total floor area",
    "建築面積": "Building area",
    "敷地面積": "Site area",
    "容積率": "Floor area ratio",
    "建ぺい率": "Building coverage ratio",
    "利回り": "Yield",
    "表面利回り": "Gross yield",
    "実質利回り": "Net yield",
    "坪単価": "Price per tsubo",
    "路線価": "Roadside land price",
    "固定資産税評価額": "Assessed value for property tax",
    "収益還元法": "Income capitalization approach",
    "原価法": "Cost approach",
    "取引事例比較法": "Sales comparison approach",
    "NOI": "NOI",
    "キャップレート": "Cap rate",
    "レントロール": "Rent roll",
    "満室想定賃料": "Potential gross rental income",
    "空室率": "Vacancy rate",
    "稼働率": "Occupancy rate",
    "管理費": "Management fee",
    "修繕積立金": "Repair reserve fund",
    "敷金": "Security deposit",
    "礼金": "Key money",
    "仲介手数料": "Brokerage fee",
    "重要事項説明": "Explanation of important matters",
    "重要事項説明書": "Explanation document of important matters",
    "登記簿謄本": "Certified copy of register",
    "所有権": "Ownership",
    "借地権": "Leasehold right",
    "定期借家契約": "Fixed-term lease agreement",
    "普通借家契約": "Ordinary lease agreement",
    "区分所有": "Condominium ownership",
    "一棟": "Whole building",
    "収益物件": "Income-producing property",
    "投資物件": "Investment property",
    "新築": "Newly built",
    "中古": "Pre-owned",
    "築年数": "Building age",
    "鉄筋コンクリート造": "Reinforced concrete",
    "鉄骨造": "Steel frame",
    "木造": "Wooden",
    "駅徒歩": "Walking distance from station",
    "間取り": "Floor plan",
}

REAL_ESTATE_JA_ZH = {
    "専有面積": "专有面积",
    "共用部": "公用部分",
    "共用部分": "公用部分",
    "延床面積": "总建筑面积",
    "建築面積": "建筑面积",
    "敷地面積": "用地面积",
    "容積率": "容积率",
    "建ぺい率": "建筑覆盖率",
    "利回り": "收益率",
    "表面利回り": "表面收益率",
    "実質利回り": "实际收益率",
    "坪単価": "每坪单价",
    "路線価": "路线价",
    "NOI": "净营业收入",
    "キャップレート": "资本化率",
    "レントロール": "租金明细表",
    "空室率": "空置率",
    "稼働率": "入住率",
    "管理費": "管理费",
    "修繕積立金": "修缮积立金",
    "敷金": "押金",
    "礼金": "礼金",
    "仲介手数料": "中介手续费",
    "所有権": "所有权",
    "借地権": "租赁土地权",
    "区分所有": "区分所有",
    "収益物件": "收益物业",
    "投資物件": "投资物业",
    "新築": "新建",
    "中古": "二手",
    "築年数": "楼龄",
    "鉄筋コンクリート造": "钢筋混凝土结构",
    "鉄骨造": "钢结构",
    "木造": "木结构",
    "間取り": "户型",
}

REAL_ESTATE_EN_JA = {v: k for k, v in REAL_ESTATE_JA_EN.items()}


def get_glossary_entries(source_lang: str, target_lang: str) -> dict[str, str] | None:
    """言語ペアに対応する用語集を返す。対応ペアがなければNone。"""
    src = source_lang.upper()
    tgt = target_lang.upper().split("-")[0]

    if src == "JA" and tgt == "EN":
        return REAL_ESTATE_JA_EN
    if src == "JA" and tgt == "ZH":
        return REAL_ESTATE_JA_ZH
    if src == "EN" and tgt == "JA":
        return REAL_ESTATE_EN_JA
    return None
