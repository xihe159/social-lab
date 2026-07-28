from __future__ import annotations

DYNAMIC_FIELDS: tuple[str, ...] = (
    "atmosphere_score",
    "pace_score",
    "pressure_level",
    "clarity_score",
    "responsiveness_score",
    "progress_score",
    "repairability_score",
    "boundary_score",
)

DYNAMIC_FIELD_NAMES: dict[str, str] = {
    "atmosphere_score": "氛围",
    "pace_score": "节奏健康度",
    "pressure_level": "压力",
    "clarity_score": "清晰度",
    "responsiveness_score": "回应度",
    "progress_score": "推进度",
    "repairability_score": "可修复性",
    "boundary_score": "边界健康度",
}

RELATIONSHIP_POLITE_WORDS = (
    "请",
    "谢谢",
    "麻烦",
    "辛苦",
    "您好",
    "抱歉",
    "不好意思",
    "please",
    "thanks",
)

DYNAMICS_POLITE_WORDS = (
    "请",
    "谢谢",
    "麻烦",
    "抱歉",
    "不好意思",
    "please",
    "thanks",
)

CONCRETE_WORDS = (
    "计划",
    "安排",
    "时间",
    "日期",
    "明天",
    "今天",
    "步骤",
    "方案",
    "补救",
    "提交",
    "deadline",
)

PRESSURE_WORDS = (
    "必须",
    "立刻",
    "马上",
    "赶紧",
    "你应该",
    "不然",
    "否则",
    "必须帮",
    "asap",
    "immediately",
)

VAGUE_WORDS = (
    "随便",
    "反正",
    "不知道",
    "你看着办",
    "没办法",
    "再说吧",
)

RESPONSIBILITY_WORDS = (
    "我会",
    "我已经",
    "我负责",
    "我承担",
    "我来处理",
    "我会补充",
    "i will",
    "i have",
)

APOLOGY_WORDS = (
    "抱歉",
    "对不起",
    "不好意思",
    "是我的问题",
    "我错了",
    "sorry",
)

GIVES_SPACE_WORDS = (
    "不方便也没关系",
    "你可以拒绝",
    "不用马上",
    "不用现在回答",
    "你先考虑",
    "有空再",
    "如果不合适",
    "不合适也没关系",
    "不方便也可以",
    "no pressure",
    "take your time",
)

EXPLICIT_ACCEPTANCE_WORDS = (
    "可以",
    "好",
    "行",
    "没问题",
    "同意",
    "愿意",
    "那就这样",
    "我答应",
)

CONDITIONAL_ACCEPTANCE_WORDS = (
    "如果",
    "先把",
    "先发",
    "再看",
    "可以考虑",
    "看情况",
    "不保证",
)

EXPLICIT_REFUSAL_WORDS = (
    "不行",
    "不能",
    "不接受",
    "不愿意",
    "不想",
    "拒绝",
    "算了",
    "不要再",
    "别再",
)

DEFENSIVE_REPLY_WORDS = (
    "有压力",
    "别逼",
    "凭什么",
    "你总是",
    "我不舒服",
    "让我很不舒服",
    "防备",
)

DETAIL_REQUEST_WORDS = (
    "具体",
    "怎么",
    "什么时候",
    "哪些",
    "为什么",
)

EXPLICIT_STOP_WORDS = (
    "不要再",
    "别再",
    "不想继续",
    "到此为止",
    "停止联系",
)

ATMOSPHERE_REFUSAL_WORDS = (
    "不行",
    "不能",
    "不接受",
    "不愿意",
    "不想",
    "拒绝",
    "算了",
)
