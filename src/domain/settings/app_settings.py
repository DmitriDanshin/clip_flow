from .boolean_setting import BooleanSetting
from .integer_setting import IntegerSetting
from .setting_metadata import SettingMetadata
from .setting_type import SettingType
from .settings import Settings
from .settings_group import SettingsGroup


def create_app_settings() -> Settings:
    max_substitutions_setting = IntegerSetting(
        SettingMetadata(
            key="fuzzy_search.max_substitutions",
            display_name="Maximum Substitutions",
            description="Maximum number of character substitutions allowed in fuzzy search. Set to None for unlimited.",
            setting_type=SettingType.INTEGER,
            default_value=None,
            min_value=0,
            max_value=10,
        )
    )

    max_insertions_setting = IntegerSetting(
        SettingMetadata(
            key="fuzzy_search.max_insertions",
            display_name="Maximum Insertions",
            description="Maximum number of character insertions allowed in fuzzy search. Set to None for unlimited.",
            setting_type=SettingType.INTEGER,
            default_value=None,
            min_value=0,
            max_value=10,
        )
    )

    max_deletions_setting = IntegerSetting(
        SettingMetadata(
            key="fuzzy_search.max_deletions",
            display_name="Maximum Deletions",
            description="Maximum number of character deletions allowed in fuzzy search. Set to None for unlimited.",
            setting_type=SettingType.INTEGER,
            default_value=None,
            min_value=0,
            max_value=10,
        )
    )

    max_l_dist_setting = IntegerSetting(
        SettingMetadata(
            key="fuzzy_search.max_l_dist",
            display_name="Maximum Levenshtein Distance",
            description="Maximum Levenshtein distance allowed in fuzzy search. Lower values mean stricter matching.",
            setting_type=SettingType.INTEGER,
            default_value=1,
            min_value=0,
            max_value=10,
        )
    )

    case_sensitive_setting = BooleanSetting(
        SettingMetadata(
            key="fuzzy_search.case_sensitive",
            display_name="Case Sensitive",
            description="Whether fuzzy search should be case sensitive or not.",
            setting_type=SettingType.BOOLEAN,
            default_value=False,
        )
    )

    fuzzy_search_group = SettingsGroup(
        name="fuzzy_search",
        display_name="Fuzzy Search",
        description="Settings for fuzzy text search functionality",
        settings={
            "fuzzy_search.max_substitutions": max_substitutions_setting,
            "fuzzy_search.max_insertions": max_insertions_setting,
            "fuzzy_search.max_deletions": max_deletions_setting,
            "fuzzy_search.max_l_dist": max_l_dist_setting,
            "fuzzy_search.case_sensitive": case_sensitive_setting,
        },
    )

    all_groups = {
        "fuzzy_search": fuzzy_search_group,
    }

    return Settings(groups=all_groups)
