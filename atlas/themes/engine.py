from dataclasses import dataclass
from enum import Enum


class Theme(str, Enum):
    AI_INFRASTRUCTURE = "AI infrastructure"
    ENERGY_TRANSITION = "Energy transition"
    ELECTRIFICATION = "Electrification"
    SEMICONDUCTORS = "Semiconductors"
    HEALTHCARE_INNOVATION = "Healthcare innovation"


@dataclass(frozen=True)
class ThemeInput:
    theme: str


@dataclass(frozen=True)
class ThemeBottleneck:
    name: str
    why_it_matters: str
    affected_industries: tuple[str, ...]


@dataclass(frozen=True)
class ThemeBeneficiary:
    name: str
    category: str
    rationale: str


@dataclass(frozen=True)
class ThemeRisk:
    name: str
    why_it_matters: str


@dataclass(frozen=True)
class ThemeAnalysis:
    theme: Theme
    summary: str
    key_bottlenecks: tuple[ThemeBottleneck, ...]
    affected_industries: tuple[str, ...]
    potential_beneficiaries: tuple[ThemeBeneficiary, ...]
    related_equities: tuple[str, ...]
    related_etfs: tuple[str, ...]
    related_commodities: tuple[str, ...]
    second_order_winners: tuple[str, ...]
    key_risks: tuple[ThemeRisk, ...]
    monitoring_items: tuple[str, ...]
    confidence: int
    what_would_change_view: tuple[str, ...]


class ThemeEngine:
    def analyze(self, theme_input: ThemeInput | str) -> ThemeAnalysis:
        requested_theme = theme_input.theme if isinstance(theme_input, ThemeInput) else theme_input
        theme = _parse_theme(requested_theme)
        return THEME_TEMPLATES[theme]

    def supported_themes(self) -> tuple[Theme, ...]:
        return tuple(Theme)


def render_theme_analysis(analysis: ThemeAnalysis) -> str:
    lines = [
        "Theme Analysis",
        "",
        f"Theme: {analysis.theme.value}",
        f"Confidence: {analysis.confidence}/100",
        "",
        "Theme Summary",
        analysis.summary,
        "",
        "Key Bottlenecks",
    ]
    for bottleneck in analysis.key_bottlenecks:
        lines.append(
            (
                f"- {bottleneck.name}: {bottleneck.why_it_matters} "
                f"Affected industries: {', '.join(bottleneck.affected_industries)}."
            )
        )
    lines.extend(
        [
            "",
            "Affected Industries",
            *_render_list(analysis.affected_industries),
            "",
            "Potential Beneficiaries",
        ]
    )
    for beneficiary in analysis.potential_beneficiaries:
        lines.append(
            f"- {beneficiary.name} ({beneficiary.category}): {beneficiary.rationale}"
        )
    lines.extend(
        [
            "",
            "Related Assets",
            "Equities",
            *_render_list(analysis.related_equities),
            "ETFs",
            *_render_list(analysis.related_etfs),
            "Commodities",
            *_render_list(analysis.related_commodities),
            "",
            "Second-Order Winners",
            *_render_list(analysis.second_order_winners),
            "",
            "Key Risks",
        ]
    )
    for risk in analysis.key_risks:
        lines.append(f"- {risk.name}: {risk.why_it_matters}")
    lines.extend(
        [
            "",
            "What Atlas Is Monitoring",
            *_render_list(analysis.monitoring_items),
            "",
            "What Would Change Atlas' View",
            *_render_list(analysis.what_would_change_view),
            "",
            "Research Framing",
            (
                "These are thematic research directions, not personalized financial "
                "recommendations or buy/sell advice."
            ),
        ]
    )
    return "\n".join(lines)


def _parse_theme(theme: str) -> Theme:
    normalized = theme.strip().lower().replace("-", " ")
    aliases = {
        "ai": Theme.AI_INFRASTRUCTURE,
        "ai infrastructure": Theme.AI_INFRASTRUCTURE,
        "artificial intelligence infrastructure": Theme.AI_INFRASTRUCTURE,
        "energy transition": Theme.ENERGY_TRANSITION,
        "electrification": Theme.ELECTRIFICATION,
        "semiconductors": Theme.SEMICONDUCTORS,
        "semiconductor": Theme.SEMICONDUCTORS,
        "healthcare innovation": Theme.HEALTHCARE_INNOVATION,
        "health care innovation": Theme.HEALTHCARE_INNOVATION,
    }
    try:
        return aliases[normalized]
    except KeyError as exc:
        supported = ", ".join(theme.value for theme in Theme)
        raise ValueError(f"Unsupported theme: {theme}. Supported themes: {supported}") from exc


def _render_list(items: tuple[str, ...]) -> list[str]:
    if not items:
        return ["- None"]
    return [f"- {item}" for item in items]


THEME_TEMPLATES: dict[Theme, ThemeAnalysis] = {
    Theme.AI_INFRASTRUCTURE: ThemeAnalysis(
        theme=Theme.AI_INFRASTRUCTURE,
        summary=(
            "AI infrastructure is a full-stack capacity buildout. The next bottlenecks "
            "are likely to move beyond chips into power, grid interconnection, data "
            "center construction, thermal management, memory bandwidth, and advanced "
            "packaging."
        ),
        key_bottlenecks=(
            ThemeBottleneck(
                name="Electricity supply",
                why_it_matters="AI data centers require large, reliable power loads.",
                affected_industries=("Utilities", "Data centers", "Power generation"),
            ),
            ThemeBottleneck(
                name="Grid capacity",
                why_it_matters="Interconnection delays can slow data center deployment.",
                affected_industries=("Utilities", "Grid equipment", "Engineering services"),
            ),
            ThemeBottleneck(
                name="Data center construction",
                why_it_matters="Physical capacity constrains how fast compute can be deployed.",
                affected_industries=("Construction", "Real estate", "Cloud infrastructure"),
            ),
            ThemeBottleneck(
                name="Cooling",
                why_it_matters="Higher rack density raises thermal management requirements.",
                affected_industries=("Thermal systems", "Industrial equipment", "Chemicals"),
            ),
            ThemeBottleneck(
                name="Transformers",
                why_it_matters="Transformer shortages can delay power delivery.",
                affected_industries=("Electrical equipment", "Utilities", "Grid services"),
            ),
            ThemeBottleneck(
                name="HBM memory",
                why_it_matters="AI accelerators depend on high bandwidth memory availability.",
                affected_industries=("Memory", "Semiconductors", "AI accelerators"),
            ),
            ThemeBottleneck(
                name="Advanced packaging",
                why_it_matters="Chiplet and accelerator scaling depends on packaging capacity.",
                affected_industries=("Semiconductor equipment", "Foundries", "Substrates"),
            ),
        ),
        affected_industries=(
            "Semiconductors",
            "Cloud computing",
            "Data centers",
            "Utilities",
            "Grid equipment",
            "Thermal management",
            "Construction and engineering",
        ),
        potential_beneficiaries=(
            ThemeBeneficiary("NVIDIA", "Equity", "AI accelerator demand leader."),
            ThemeBeneficiary("TSMC", "Equity", "Advanced node and packaging exposure."),
            ThemeBeneficiary("SK hynix", "Equity", "HBM memory exposure."),
            ThemeBeneficiary("Vertiv", "Equity", "Data center power and cooling exposure."),
            ThemeBeneficiary("Eaton", "Equity", "Electrical infrastructure exposure."),
            ThemeBeneficiary(
                "Utilities with available power",
                "Industry",
                "Power scarcity can raise strategic value.",
            ),
        ),
        related_equities=("NVDA", "TSM", "AMD", "AVGO", "VRT", "ETN", "SMCI"),
        related_etfs=("SMH", "SOXX", "AIQ", "CIBR"),
        related_commodities=("Copper", "Natural gas", "Uranium"),
        second_order_winners=(
            "Grid modernization suppliers",
            "Industrial cooling vendors",
            "Power management companies",
            "Specialty construction firms",
            "Memory supply chain participants",
        ),
        key_risks=(
            ThemeRisk("Overcapacity", "Infrastructure can be overbuilt if AI demand disappoints."),
            ThemeRisk("Power constraints", "Lack of power can delay revenue conversion."),
            ThemeRisk("Margin compression", "Competition can reduce hardware economics over time."),
            ThemeRisk(
                "Regulation",
                "Energy use, data privacy, and export controls can alter returns.",
            ),
        ),
        monitoring_items=(
            "Data center power purchase agreements",
            "Grid interconnection queues",
            "HBM supply and pricing",
            "Advanced packaging capacity",
            "Cloud capex guidance",
            "AI workload monetization",
        ),
        confidence=88,
        what_would_change_view=(
            "AI workload growth slows materially.",
            "Cloud providers reduce capex plans.",
            "Power and grid constraints resolve faster than expected.",
            "Accelerator supply materially exceeds demand.",
        ),
    ),
    Theme.ENERGY_TRANSITION: ThemeAnalysis(
        theme=Theme.ENERGY_TRANSITION,
        summary=(
            "Energy transition is a multi-decade shift in generation, storage, grid "
            "infrastructure, and industrial efficiency. Bottlenecks often appear in "
            "permitting, grid capacity, storage duration, and critical minerals."
        ),
        key_bottlenecks=(
            ThemeBottleneck(
                "Permitting",
                "Projects can be delayed by approvals.",
                ("Renewables", "Transmission"),
            ),
            ThemeBottleneck(
                "Transmission",
                "Clean power needs grid access.",
                ("Utilities", "Grid equipment"),
            ),
            ThemeBottleneck(
                "Storage",
                "Intermittent generation requires flexibility.",
                ("Batteries", "Power markets"),
            ),
            ThemeBottleneck(
                "Critical minerals",
                "Supply chains can constrain scaling.",
                ("Mining", "Battery materials"),
            ),
        ),
        affected_industries=(
            "Utilities",
            "Renewable developers",
            "Grid equipment",
            "Battery storage",
            "Mining",
            "Industrial efficiency",
        ),
        potential_beneficiaries=(
            ThemeBeneficiary("NextEra Energy", "Equity", "Renewables and utility exposure."),
            ThemeBeneficiary("Eaton", "Equity", "Electrical infrastructure exposure."),
            ThemeBeneficiary("Quanta Services", "Equity", "Grid construction exposure."),
            ThemeBeneficiary(
                "Copper producers",
                "Industry",
                "Electrification increases copper demand.",
            ),
        ),
        related_equities=("NEE", "ETN", "PWR", "FSLR", "ENPH"),
        related_etfs=("ICLN", "QCLN", "GRID"),
        related_commodities=("Copper", "Lithium", "Uranium", "Silver"),
        second_order_winners=(
            "Transmission builders",
            "Industrial software providers",
            "Battery recyclers",
            "Power electronics suppliers",
        ),
        key_risks=(
            ThemeRisk("Policy volatility", "Subsidies and rules can change economics."),
            ThemeRisk("Commodity cycles", "Input cost swings can pressure margins."),
            ThemeRisk("Project delays", "Permitting and grid queues can defer returns."),
        ),
        monitoring_items=(
            "Transmission buildout",
            "Power storage costs",
            "Policy incentives",
            "Critical mineral supply",
        ),
        confidence=82,
        what_would_change_view=(
            "Policy support weakens materially.",
            "Storage economics fail to improve.",
            "Grid investment slows.",
        ),
    ),
    Theme.ELECTRIFICATION: ThemeAnalysis(
        theme=Theme.ELECTRIFICATION,
        summary=(
            "Electrification shifts energy demand toward electrical systems across "
            "transport, buildings, industry, and computing. The pressure points are "
            "grid capacity, power electronics, copper, transformers, and charging."
        ),
        key_bottlenecks=(
            ThemeBottleneck(
                "Copper supply",
                "Electrical systems are copper intensive.",
                ("Mining", "Electrical equipment"),
            ),
            ThemeBottleneck(
                "Transformers",
                "Distribution equipment can delay upgrades.",
                ("Utilities", "Grid equipment"),
            ),
            ThemeBottleneck(
                "Charging infrastructure",
                "Adoption requires reliable access.",
                ("EVs", "Real estate"),
            ),
            ThemeBottleneck(
                "Power electronics",
                "Efficiency depends on advanced components.",
                ("Semiconductors", "Industrials"),
            ),
        ),
        affected_industries=(
            "Electrical equipment",
            "Automotive",
            "Utilities",
            "Semiconductors",
            "Mining",
            "Industrial automation",
        ),
        potential_beneficiaries=(
            ThemeBeneficiary("Eaton", "Equity", "Power distribution exposure."),
            ThemeBeneficiary("Schneider Electric", "Equity", "Energy management exposure."),
            ThemeBeneficiary("ON Semiconductor", "Equity", "Power semiconductor exposure."),
            ThemeBeneficiary("Copper miners", "Industry", "Electrification demand support."),
        ),
        related_equities=("ETN", "SBGSY", "ON", "ALB", "FCX"),
        related_etfs=("GRID", "DRIV", "COPX"),
        related_commodities=("Copper", "Lithium", "Nickel"),
        second_order_winners=(
            "Electrical contractors",
            "Charging software platforms",
            "Grid analytics providers",
            "Industrial automation suppliers",
        ),
        key_risks=(
            ThemeRisk("Adoption timing", "EV and industrial demand can be cyclical."),
            ThemeRisk("Grid delays", "Infrastructure can lag demand."),
            ThemeRisk("Commodity volatility", "Input costs can change project economics."),
        ),
        monitoring_items=(
            "EV penetration",
            "Grid upgrade spending",
            "Copper inventories",
            "Transformer lead times",
        ),
        confidence=80,
        what_would_change_view=(
            "Electrification adoption slows materially.",
            "Copper substitution reduces demand intensity.",
            "Grid investment falls short for several years.",
        ),
    ),
    Theme.SEMICONDUCTORS: ThemeAnalysis(
        theme=Theme.SEMICONDUCTORS,
        summary=(
            "Semiconductors are the enabling layer for compute, AI, autos, industrial "
            "automation, and communications. Bottlenecks rotate between leading-edge "
            "capacity, memory, equipment, substrates, and geopolitical access."
        ),
        key_bottlenecks=(
            ThemeBottleneck(
                "Leading-edge foundry capacity",
                "Advanced chips need scarce fabs.",
                ("Foundries", "AI accelerators"),
            ),
            ThemeBottleneck(
                "Lithography and equipment",
                "Tooling controls production scaling.",
                ("Equipment", "Foundries"),
            ),
            ThemeBottleneck(
                "HBM memory",
                "AI systems need memory bandwidth.",
                ("Memory", "Accelerators"),
            ),
            ThemeBottleneck(
                "Substrates and packaging",
                "Advanced packages need specialized supply.",
                ("Packaging", "Materials"),
            ),
        ),
        affected_industries=(
            "Foundries",
            "Semiconductor equipment",
            "Memory",
            "EDA software",
            "Advanced packaging",
            "Electronics manufacturing",
        ),
        potential_beneficiaries=(
            ThemeBeneficiary("ASML", "Equity", "Critical lithography exposure."),
            ThemeBeneficiary("TSMC", "Equity", "Leading-edge foundry exposure."),
            ThemeBeneficiary("Applied Materials", "Equity", "Semiconductor equipment exposure."),
            ThemeBeneficiary("Synopsys", "Equity", "EDA software exposure."),
        ),
        related_equities=("ASML", "TSM", "AMAT", "LRCX", "SNPS", "CDNS", "MU"),
        related_etfs=("SMH", "SOXX"),
        related_commodities=("Silicon", "Copper", "Rare gases"),
        second_order_winners=(
            "EDA software vendors",
            "Specialty materials suppliers",
            "Advanced substrate makers",
            "Semiconductor testing firms",
        ),
        key_risks=(
            ThemeRisk("Cycle risk", "Inventory corrections can be severe."),
            ThemeRisk("Geopolitics", "Export controls and Taiwan risk can reshape supply."),
            ThemeRisk("Capex digestion", "Overbuilding can pressure utilization."),
        ),
        monitoring_items=(
            "Foundry utilization",
            "Memory pricing",
            "Equipment order books",
            "Export control changes",
        ),
        confidence=86,
        what_would_change_view=(
            "AI semiconductor demand slows sharply.",
            "Memory pricing deteriorates.",
            "New restrictions disrupt key supply chains.",
        ),
    ),
    Theme.HEALTHCARE_INNOVATION: ThemeAnalysis(
        theme=Theme.HEALTHCARE_INNOVATION,
        summary=(
            "Healthcare innovation spans drug discovery, biologics, devices, diagnostics, "
            "AI-enabled workflows, and care delivery. Bottlenecks often involve clinical "
            "validation, reimbursement, regulation, and manufacturing scale."
        ),
        key_bottlenecks=(
            ThemeBottleneck(
                "Clinical validation",
                "Adoption requires evidence.",
                ("Biotech", "Medtech", "Diagnostics"),
            ),
            ThemeBottleneck(
                "Regulatory approval",
                "Timelines affect commercialization.",
                ("Pharma", "Devices"),
            ),
            ThemeBottleneck(
                "Reimbursement",
                "Payment rules determine adoption speed.",
                ("Providers", "Diagnostics"),
            ),
            ThemeBottleneck(
                "Manufacturing scale",
                "Biologics and devices need reliable production.",
                ("CDMOs", "Medtech"),
            ),
        ),
        affected_industries=(
            "Biopharma",
            "Medical devices",
            "Diagnostics",
            "Life science tools",
            "Healthcare software",
            "Contract manufacturing",
        ),
        potential_beneficiaries=(
            ThemeBeneficiary("Eli Lilly", "Equity", "Innovation-led pharma exposure."),
            ThemeBeneficiary("Thermo Fisher", "Equity", "Life science tools exposure."),
            ThemeBeneficiary("Intuitive Surgical", "Equity", "Robotic surgery exposure."),
            ThemeBeneficiary("Danaher", "Equity", "Diagnostics and life sciences exposure."),
        ),
        related_equities=("LLY", "TMO", "ISRG", "DHR", "VRTX", "REGN"),
        related_etfs=("XLV", "IBB", "XBI", "IHI"),
        related_commodities=(),
        second_order_winners=(
            "Clinical trial software providers",
            "Specialty manufacturers",
            "Diagnostics platforms",
            "Healthcare data infrastructure",
        ),
        key_risks=(
            ThemeRisk("Trial failure", "Clinical risk can erase expected value."),
            ThemeRisk("Reimbursement pressure", "Payers can limit adoption."),
            ThemeRisk("Regulatory delays", "Approval timelines can shift materially."),
        ),
        monitoring_items=(
            "Clinical readouts",
            "FDA decisions",
            "Reimbursement updates",
            "Procedure volumes",
            "R&D productivity",
        ),
        confidence=78,
        what_would_change_view=(
            "Major clinical programs disappoint.",
            "Pricing pressure increases materially.",
            "Regulatory pathways become slower or less predictable.",
        ),
    ),
}
