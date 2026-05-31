"""
Seed corpus for the M3 Art-history RAG.

~20 short snippets covering Tang/Song/Yuan/Ming/Qing painting:
literati landscape, bird-and-flower, Northern vs Southern Song style,
court painting, and a few key painters (Fan Kuan, Mi Youren, Bada Shanren, etc.).

These are deliberately short, paraphrased, public-domain-style summaries
written for the demo. In production this list would be replaced by snippets
extracted from museum descriptions, art-history textbooks and KG entries
(see proposal §3.2.4).
"""

SEED_CHUNKS: list[dict] = [
    # ---------------- Tang ----------------
    {
        "text": (
            "Tang dynasty painting is marked by vigorous figure painting and "
            "the rise of blue-and-green landscape (qinglu shanshui). Court "
            "painters such as Yan Liben and Wu Daozi emphasise narrative, "
            "lineage and Buddhist-Daoist iconography, with strong outlines "
            "and saturated mineral pigments."
        ),
        "dynasty": "Tang",
        "painter": None,
        "school": "Court / blue-and-green landscape",
        "motif": "figures; bodhisattvas; courtly scenes",
        "source": "seed:tang-overview",
    },
    {
        "text": (
            "Li Sixun and his son Li Zhaodao codify the blue-and-green "
            "landscape style of the Tang court: meticulous outlines filled "
            "with azurite and malachite, often depicting palace complexes "
            "tucked into stylised peaks. The mood is decorative, monumental "
            "and aristocratic rather than meditative."
        ),
        "dynasty": "Tang",
        "painter": "Li Sixun; Li Zhaodao",
        "school": "Blue-and-green landscape",
        "motif": "palaces; peaks; mineral pigments",
        "source": "seed:tang-blue-green",
    },

    # ---------------- Five Dynasties / Northern Song ----------------
    {
        "text": (
            "Northern Song monumental landscape, exemplified by Fan Kuan's "
            "'Travelers Among Mountains and Streams', uses a towering central "
            "peak, dense raindrop texture strokes (yu dian cun) and a tiny "
            "human figure to convey cosmic scale and the Confucian-Daoist "
            "ideal of nature dwarfing humanity."
        ),
        "dynasty": "Northern Song",
        "painter": "Fan Kuan",
        "school": "Monumental landscape",
        "motif": "towering peak; mist; tiny travellers",
        "source": "seed:fan-kuan",
    },
    {
        "text": (
            "Guo Xi's 'Early Spring' (1072) develops the Northern Song "
            "'crab-claw' tree branches and 'devil-face' rock contours into a "
            "shifting, atmospheric world of mist and thaw. His treatise 'The "
            "Lofty Message of Forests and Streams' theorises the three "
            "distances -- high, deep and level -- as compositional devices."
        ),
        "dynasty": "Northern Song",
        "painter": "Guo Xi",
        "school": "Monumental landscape",
        "motif": "mist; spring thaw; crab-claw branches",
        "source": "seed:guo-xi",
    },
    {
        "text": (
            "Li Cheng, active in the early Northern Song, paints sparse "
            "wintry plains, leafless trees and distant temples on flat "
            "horizons. His restrained ink tonalities and emphasis on cold, "
            "vacant space deeply influence later literati landscape painters."
        ),
        "dynasty": "Northern Song",
        "painter": "Li Cheng",
        "school": "Monumental landscape",
        "motif": "wintry plain; bare trees; empty distance",
        "source": "seed:li-cheng",
    },

    # ---------------- Southern Song ----------------
    {
        "text": (
            "Southern Song academy painters Ma Yuan and Xia Gui develop the "
            "'one-corner' (Ma yi jiao) and 'half-side' (Xia ban bian) "
            "compositions: a heavy motif anchored in one corner and vast "
            "washes of mist or water occupying the rest. The mood is "
            "intimate, lyrical, melancholic -- a clear shift from Northern "
            "Song monumentality."
        ),
        "dynasty": "Southern Song",
        "painter": "Ma Yuan; Xia Gui",
        "school": "Southern Song academy",
        "motif": "one-corner composition; mist; lone figure",
        "source": "seed:ma-xia",
    },
    {
        "text": (
            "Mi Youren, son of Mi Fu, continues the 'Mi family cloud-mountain' "
            "style of the late Northern and Southern Song: horizontal layered "
            "ink dots ('Mi dian') for foliage and ridges seen through "
            "drifting mist, with almost no contour lines. The result is "
            "fluid, dreamy and proto-impressionistic."
        ),
        "dynasty": "Southern Song",
        "painter": "Mi Youren",
        "school": "Mi family cloud-mountain",
        "motif": "cloud-mountains; ink dots; drifting mist",
        "source": "seed:mi-youren",
    },
    {
        "text": (
            "The Chan-Buddhist painter Muqi (Fachang), active in late "
            "Southern Song Hangzhou, paints monochrome ink studies of "
            "persimmons, monkeys and Bodhidharma with spontaneous, "
            "asymmetric brushwork. His works become canonical in Japanese "
            "Zen aesthetics."
        ),
        "dynasty": "Southern Song",
        "painter": "Muqi",
        "school": "Chan-Buddhist ink painting",
        "motif": "persimmons; gibbons; meditation",
        "source": "seed:muqi",
    },

    # ---------------- Yuan ----------------
    {
        "text": (
            "Under Mongol rule, many Han literati withdraw from office and "
            "reframe painting as personal expression. The Yuan 'four masters' "
            "-- Huang Gongwang, Wu Zhen, Ni Zan and Wang Meng -- prize dry "
            "brush, calligraphic line and self-inscribed poems over courtly "
            "polish, establishing literati (wenrenhua) painting as the "
            "dominant idiom."
        ),
        "dynasty": "Yuan",
        "painter": "Huang Gongwang; Wu Zhen; Ni Zan; Wang Meng",
        "school": "Literati / wenrenhua",
        "motif": "dry brush; reclusive landscape; inscriptions",
        "source": "seed:yuan-four-masters",
    },
    {
        "text": (
            "Ni Zan's landscapes are famously austere: a few sparse trees, a "
            "small empty pavilion, a strip of water and distant low hills, "
            "all rendered with a dry, restrained brush. There are almost "
            "never any human figures, and the mood is detached, cool and "
            "withdrawn -- a visual emblem of late-Yuan literati exile."
        ),
        "dynasty": "Yuan",
        "painter": "Ni Zan",
        "school": "Literati / wenrenhua",
        "motif": "empty pavilion; sparse trees; no figures",
        "source": "seed:ni-zan",
    },
    {
        "text": (
            "Huang Gongwang's 'Dwelling in the Fuchun Mountains' is painted "
            "over several years as a continuous handscroll. Its varied dry "
            "brushwork and unhurried rhythm of ridges and rivers exemplify "
            "the Yuan ideal of landscape as a record of lived experience and "
            "inner cultivation, not topographic accuracy."
        ),
        "dynasty": "Yuan",
        "painter": "Huang Gongwang",
        "school": "Literati / wenrenhua",
        "motif": "handscroll; Fuchun river; dry brush",
        "source": "seed:huang-gongwang",
    },

    # ---------------- Ming ----------------
    {
        "text": (
            "The Ming Wu school, centred in Suzhou and led by Shen Zhou and "
            "Wen Zhengming, revives the Yuan literati lineage. Their works "
            "combine refined ink with cultivated colour, depict the gardens "
            "and villas of the Jiangnan elite, and place strong emphasis on "
            "self-inscribed poems and friendship paintings."
        ),
        "dynasty": "Ming",
        "painter": "Shen Zhou; Wen Zhengming",
        "school": "Wu school",
        "motif": "Jiangnan gardens; friendship; inscriptions",
        "source": "seed:wu-school",
    },
    {
        "text": (
            "The rival Ming Zhe school, led by Dai Jin, looks back to "
            "Southern Song academy painters Ma Yuan and Xia Gui. It "
            "preserves more dramatic brushwork, stronger ink contrasts and "
            "professional-painter polish, in contrast to the Wu school's "
            "amateur-literati ethos."
        ),
        "dynasty": "Ming",
        "painter": "Dai Jin",
        "school": "Zhe school",
        "motif": "dramatic brushwork; Ma-Xia revival",
        "source": "seed:zhe-school",
    },
    {
        "text": (
            "Ming bird-and-flower painting flourishes in two registers: the "
            "decorative court mode of Lü Ji, with meticulous polychrome "
            "phoenixes, peonies and pines, and the freer xieyi mode of Xu "
            "Wei, whose splashed-ink grapes and banana leaves anticipate "
            "early-Qing individualists."
        ),
        "dynasty": "Ming",
        "painter": "Lü Ji; Xu Wei",
        "school": "Bird-and-flower",
        "motif": "peonies; phoenix; splashed ink",
        "source": "seed:ming-birds-flowers",
    },

    # ---------------- Qing ----------------
    {
        "text": (
            "Early-Qing 'individualist' monk-painters such as Bada Shanren "
            "(Zhu Da) and Shitao react against orthodoxy with eccentric "
            "compositions, asymmetric brushwork and ironic motifs -- "
            "glaring-eyed birds and fish, distorted lotuses, splashed-ink "
            "rocks. Their works carry strong personal and political "
            "subtext as Ming loyalists under Qing rule."
        ),
        "dynasty": "Qing",
        "painter": "Bada Shanren; Shitao",
        "school": "Individualists",
        "motif": "glaring birds; eccentric brush; lotus",
        "source": "seed:bada-shitao",
    },
    {
        "text": (
            "The 'Four Wangs' of the early Qing -- Wang Shimin, Wang Jian, "
            "Wang Hui, Wang Yuanqi -- consolidate orthodox literati "
            "landscape by systematically copying and re-combining the Yuan "
            "and Ming masters. Their work is technically refined and "
            "court-favoured, often described as conservative and synthetic "
            "rather than innovative."
        ),
        "dynasty": "Qing",
        "painter": "Wang Shimin; Wang Jian; Wang Hui; Wang Yuanqi",
        "school": "Orthodox literati",
        "motif": "synthetic landscape; copying old masters",
        "source": "seed:four-wangs",
    },
    {
        "text": (
            "The eighteenth-century 'Eight Eccentrics of Yangzhou' (Yangzhou "
            "baguai), including Zheng Xie and Jin Nong, paint bamboo, "
            "orchids, plum blossoms and rocks in a vigorous, calligraphic, "
            "market-oriented manner. They are professional literati selling "
            "to a wealthy merchant class, blurring the amateur/professional "
            "boundary."
        ),
        "dynasty": "Qing",
        "painter": "Zheng Xie; Jin Nong",
        "school": "Yangzhou Eccentrics",
        "motif": "bamboo; orchid; plum; calligraphic brush",
        "source": "seed:yangzhou-eccentrics",
    },

    # ---------------- Cross-cutting / aesthetic vocabulary ----------------
    {
        "text": (
            "Chinese landscape painting (shanshui) is structured by the "
            "interaction of mountain and water, void and form, near and far. "
            "Empty space (liubai) is not background but an active "
            "compositional element, suggesting mist, sky or qi, and is "
            "tightly linked to Daoist ideas of emptiness and breath."
        ),
        "dynasty": None,
        "painter": None,
        "school": "Shanshui (general)",
        "motif": "mountain and water; empty space; qi",
        "source": "seed:shanshui-aesthetics",
    },
    {
        "text": (
            "Traditional Chinese bird-and-flower painting (huaniao) is "
            "highly symbolic: plum, orchid, bamboo and chrysanthemum form "
            "the 'Four Gentlemen' embodying moral virtues; peonies suggest "
            "wealth and honour; cranes and pines suggest longevity; lotus "
            "suggests purity. Soundtracks evoking these works often lean "
            "toward gentle, decorative or auspicious affect."
        ),
        "dynasty": None,
        "painter": None,
        "school": "Bird-and-flower (general)",
        "motif": "plum; orchid; bamboo; chrysanthemum; peony; crane",
        "source": "seed:huaniao-symbols",
    },
    {
        "text": (
            "Common instrumental associations in Chinese-painting-inspired "
            "music: guqin and xiao for quiet literati landscape (low arousal, "
            "neutral-to-positive valence); pipa and erhu for narrative or "
            "melancholic scenes (mid arousal, lower valence); dizi, "
            "sheng and percussion for festive court or genre scenes "
            "(higher arousal, positive valence)."
        ),
        "dynasty": None,
        "painter": None,
        "school": "Music-aesthetic mapping",
        "motif": "guqin; xiao; pipa; erhu; dizi; sheng",
        "source": "seed:instrument-mapping",
    },
]
