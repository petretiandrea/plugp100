import dataclasses
from typing import Optional, List


@dataclasses.dataclass
class LightEffect:
    id: str
    name: str
    display_colors: List[List[int]]
    enable: int
    brightness: int = (100,)
    bAdjusted: Optional[int] = None
    brightness_range: List[int] = dataclasses.field(default_factory=list)
    backgrounds: List[List[int]] = dataclasses.field(default_factory=list)
    custom: Optional[int] = None
    direction: Optional[int] = None
    duration: Optional[int] = None
    expansion_strategy: Optional[int] = None
    fadeoff: Optional[int] = None
    hue_range: Optional[List[int]] = None
    init_states: List[List[int]] = dataclasses.field(default_factory=list)
    random_seed: Optional[int] = None
    repeat_times: Optional[int] = None
    saturation_range: Optional[List[int]] = None
    segment_length: Optional[int] = None
    segments: Optional[List[int]] = None
    sequence: Optional[List[List[int]]] = None
    spread: Optional[int] = None
    transition: Optional[int] = None
    transition_range: Optional[List[int]] = None
    type: Optional[str] = None
    trans_sequence: Optional[List[int]] = None
    run_time: Optional[int] = None

    def as_dict(self):  # custom as_dict that remove None fields
        return {k: v for k, v in dataclasses.asdict(self).items() if v is not None}

    @staticmethod
    def bubbling_calderon() -> "LightEffect":
        return LightEffect(
            id="TapoStrip_6DlumDwO2NdfHppy50vJtu",
            name="Bubbling Cauldron",
            brightness=100,
            display_colors=[[100, 100, 100], [270, 100, 100]],
            enable=1,
            bAdjusted=None,
            brightness_range=[50, 100],
            backgrounds=[[270, 40, 50]],
            custom=0,
            direction=None,
            duration=0,
            expansion_strategy=1,
            fadeoff=1000,
            hue_range=[100, 270],
            init_states=[[270, 100, 100]],
            random_seed=24,
            repeat_times=None,
            saturation_range=[80, 100],
            segment_length=None,
            segments=[0],
            sequence=None,
            spread=None,
            transition=200,
            transition_range=None,
            type="random",
            trans_sequence=None,
            run_time=None,
        )

    @staticmethod
    def aurora() -> "LightEffect":
        return LightEffect(
            id="TapoStrip_1MClvV18i15Jq3bvJVf0eP",
            name="Aurora",
            brightness=100,
            display_colors=[
                [120, 100, 100],
                [240, 100, 100],
                [260, 100, 100],
                [280, 100, 100],
            ],
            enable=1,
            bAdjusted=None,
            brightness_range=[],
            backgrounds=[],
            custom=0,
            direction=4,
            duration=0,
            expansion_strategy=1,
            fadeoff=None,
            hue_range=None,
            init_states=[],
            random_seed=None,
            repeat_times=0,
            saturation_range=None,
            segment_length=None,
            segments=[0],
            sequence=[
                [120, 100, 100],
                [240, 100, 100],
                [260, 100, 100],
                [280, 100, 100],
            ],
            spread=7,
            transition=1500,
            transition_range=None,
            type="sequence",
            trans_sequence=None,
            run_time=None,
        )

    @staticmethod
    def candy_cane() -> "LightEffect":
        return LightEffect(
            id="TapoStrip_6Dy0Nc45vlhFPEzG021Pe9",
            name="Candy Cane",
            brightness=100,
            display_colors=[[0, 0, 100], [360, 81, 100]],
            enable=1,
            bAdjusted=None,
            brightness_range=[],
            backgrounds=[],
            custom=0,
            direction=1,
            duration=700,
            expansion_strategy=1,
            fadeoff=None,
            hue_range=None,
            init_states=[],
            random_seed=None,
            repeat_times=0,
            saturation_range=None,
            segment_length=None,
            segments=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
            sequence=[
                [0, 0, 100],
                [0, 0, 100],
                [360, 81, 100],
                [0, 0, 100],
                [0, 0, 100],
                [360, 81, 100],
                [360, 81, 100],
                [0, 0, 100],
                [0, 0, 100],
                [360, 81, 100],
                [360, 81, 100],
                [360, 81, 100],
                [360, 81, 100],
                [0, 0, 100],
                [0, 0, 100],
                [360, 81, 100],
            ],
            spread=1,
            transition=500,
            transition_range=None,
            type="sequence",
        )

    @staticmethod
    def christmas() -> "LightEffect":
        return LightEffect(
            id="TapoStrip_5zkiG6avJ1IbhjiZbRlWvh",
            name="Christmas",
            brightness=100,
            display_colors=[[136, 98, 100], [350, 97, 100]],
            enable=1,
            bAdjusted=None,
            brightness_range=[50, 100],
            backgrounds=[[136, 98, 75], [136, 0, 0], [350, 0, 100], [350, 97, 94]],
            custom=0,
            direction=None,
            duration=5000,
            expansion_strategy=1,
            fadeoff=2000,
            hue_range=[136, 146],
            init_states=[[136, 0, 100]],
            random_seed=100,
            repeat_times=None,
            saturation_range=[90, 100],
            segment_length=None,
            segments=[0],
            sequence=None,
            spread=None,
            transition=0,
            transition_range=None,
            type="random",
        )

    @staticmethod
    def flicker() -> "LightEffect":
        return LightEffect(
            id="TapoStrip_4HVKmMc6vEzjm36jXaGwMs",
            name="Flicker",
            brightness=100,
            display_colors=[[30, 81, 100], [40, 100, 100]],
            enable=1,
            bAdjusted=None,
            brightness_range=[50, 100],
            backgrounds=[],
            custom=0,
            direction=None,
            duration=0,
            expansion_strategy=1,
            fadeoff=None,
            hue_range=[30, 40],
            init_states=[[30, 81, 80]],
            random_seed=None,
            repeat_times=None,
            saturation_range=[100, 100],
            segment_length=None,
            segments=[1],
            sequence=None,
            spread=None,
            transition=0,
            transition_range=[375, 500],
            type="random",
        )

    @staticmethod
    def christmas_light() -> "LightEffect":
        return LightEffect(
            id="TapoStrip_3Gk6CmXOXbjCiwz9iD543C",
            name="Grandma's Christmas Lights",
            brightness=100,
            display_colors=[
                [30, 100, 100],
                [240, 100, 100],
                [130, 100, 100],
                [0, 100, 100],
            ],
            enable=1,
            bAdjusted=None,
            brightness_range=[],
            backgrounds=[],
            custom=0,
            direction=1,
            duration=5000,
            expansion_strategy=1,
            fadeoff=None,
            hue_range=None,
            init_states=[],
            random_seed=None,
            repeat_times=0,
            saturation_range=None,
            segment_length=None,
            segments=[0],
            sequence=[
                [30, 100, 100],
                [30, 0, 0],
                [30, 0, 0],
                [240, 100, 100],
                [240, 0, 0],
                [240, 0, 0],
                [240, 0, 100],
                [240, 0, 0],
                [240, 0, 0],
                [130, 100, 100],
                [130, 0, 0],
                [130, 0, 0],
                [0, 100, 100],
                [0, 0, 0],
                [0, 0, 0],
            ],
            spread=1,
            transition=100,
            transition_range=None,
            type="sequence",
        )

    @staticmethod
    def hanukkah() -> "LightEffect":
        return LightEffect(
            id="TapoStrip_2YTk4wramLKv5XZ9KFDVYm",
            name="Hanukkah",
            brightness=100,
            display_colors=[[200, 100, 100]],
            enable=1,
            bAdjusted=None,
            brightness_range=[50, 100],
            backgrounds=[],
            custom=0,
            direction=None,
            duration=1500,
            expansion_strategy=1,
            fadeoff=None,
            hue_range=[200, 210],
            init_states=[[35, 81, 80]],
            random_seed=None,
            repeat_times=None,
            saturation_range=[0, 100],
            segment_length=None,
            segments=[1],
            sequence=None,
            spread=None,
            transition=0,
            transition_range=[400, 500],
            type="random",
        )

    @staticmethod
    def haunted_mansion() -> "LightEffect":
        return LightEffect(
            id="TapoStrip_4rJ6JwC7I9st3tQ8j4lwlI",
            name="Haunted Mansion",
            brightness=100,
            display_colors=[[45, 10, 100]],
            enable=1,
            bAdjusted=None,
            brightness_range=[0, 80],
            backgrounds=[[45, 10, 100]],
            custom=0,
            direction=None,
            duration=0,
            expansion_strategy=2,
            fadeoff=200,
            hue_range=[45, 45],
            init_states=[[45, 10, 100]],
            random_seed=1,
            repeat_times=None,
            saturation_range=[10, 10],
            segment_length=None,
            segments=[80],
            sequence=None,
            spread=None,
            transition=0,
            transition_range=[50, 1500],
            type="random",
        )

    @staticmethod
    def icicle() -> "LightEffect":
        return LightEffect(
            id="TapoStrip_7UcYLeJbiaxVIXCxr21tpx",
            name="Icicle",
            brightness=100,
            display_colors=[[190, 100, 100]],
            enable=1,
            bAdjusted=None,
            brightness_range=[],
            backgrounds=[],
            custom=0,
            direction=4,
            duration=0,
            expansion_strategy=1,
            fadeoff=None,
            hue_range=None,
            init_states=[],
            random_seed=None,
            repeat_times=0,
            saturation_range=None,
            segment_length=None,
            segments=[0],
            sequence=[
                [190, 100, 70],
                [190, 100, 70],
                [190, 30, 50],
                [190, 100, 70],
                [190, 100, 70],
            ],
            spread=3,
            transition=400,
            transition_range=None,
            type="sequence",
        )

    @staticmethod
    def lightning() -> "LightEffect":
        return LightEffect(
            id="TapoStrip_7OGzfSfnOdhoO2ri4gOHWn",
            name="Lightning",
            brightness=100,
            display_colors=[[210, 10, 100], [200, 50, 100], [200, 100, 100]],
            enable=1,
            bAdjusted=None,
            brightness_range=[90, 100],
            backgrounds=[[200, 100, 100], [200, 50, 10], [210, 10, 50], [240, 10, 0]],
            custom=0,
            direction=None,
            duration=0,
            expansion_strategy=1,
            fadeoff=150,
            hue_range=[240, 240],
            init_states=[[240, 30, 100]],
            random_seed=600,
            repeat_times=None,
            saturation_range=[10, 11],
            segment_length=None,
            segments=[7, 20, 23, 32, 34, 35, 49, 65, 66, 74, 80],
            sequence=None,
            spread=None,
            transition=50,
            transition_range=None,
            type="random",
        )

    @staticmethod
    def ocean() -> "LightEffect":
        return LightEffect(
            id="TapoStrip_0fOleCdwSgR0nfjkReeYfw",
            name="Ocean",
            brightness=100,
            display_colors=[[198, 84, 100]],
            enable=1,
            bAdjusted=None,
            brightness_range=[],
            backgrounds=[],
            custom=0,
            direction=3,
            duration=0,
            expansion_strategy=1,
            fadeoff=None,
            hue_range=None,
            init_states=[],
            random_seed=None,
            repeat_times=0,
            saturation_range=None,
            segment_length=None,
            segments=[0],
            sequence=[[198, 84, 30], [198, 70, 30], [198, 10, 30]],
            spread=16,
            transition=2000,
            transition_range=None,
            type="sequence",
        )

    @staticmethod
    def rainbow() -> "LightEffect":
        return LightEffect(
            id="TapoStrip_7CC5y4lsL8pETYvmz7UOpQ",
            name="Rainbow",
            brightness=100,
            display_colors=[
                [0, 100, 100],
                [100, 100, 100],
                [200, 100, 100],
                [300, 100, 100],
            ],
            enable=1,
            bAdjusted=None,
            brightness_range=[],
            backgrounds=[],
            custom=0,
            direction=1,
            duration=0,
            expansion_strategy=1,
            fadeoff=None,
            hue_range=None,
            init_states=[],
            random_seed=None,
            repeat_times=0,
            saturation_range=None,
            segment_length=None,
            segments=[0],
            sequence=[[0, 100, 100], [100, 100, 100], [200, 100, 100], [300, 100, 100]],
            spread=12,
            transition=1500,
            transition_range=None,
            type="sequence",
        )

    @staticmethod
    def raindrop() -> "LightEffect":
        return LightEffect(
            id="TapoStrip_1t2nWlTBkV8KXBZ0TWvBjs",
            name="Raindrop",
            brightness=100,
            display_colors=[[200, 10, 100], [200, 20, 100]],
            enable=1,
            bAdjusted=None,
            brightness_range=[10, 30],
            backgrounds=[[200, 40, 0]],
            custom=0,
            direction=None,
            duration=0,
            expansion_strategy=1,
            fadeoff=1000,
            hue_range=[200, 200],
            init_states=[[200, 40, 100]],
            random_seed=24,
            repeat_times=None,
            saturation_range=[10, 20],
            segment_length=None,
            segments=[0],
            sequence=None,
            spread=None,
            transition=1000,
            transition_range=None,
            type="random",
        )

    @staticmethod
    def spring() -> "LightEffect":
        return LightEffect(
            id="TapoStrip_1nL6GqZ5soOxj71YDJOlZL",
            name="Spring",
            brightness=100,
            display_colors=[[0, 30, 100], [130, 100, 100]],
            enable=1,
            bAdjusted=None,
            brightness_range=[90, 100],
            backgrounds=[[130, 100, 40]],
            custom=0,
            direction=None,
            duration=600,
            expansion_strategy=1,
            fadeoff=1000,
            hue_range=[0, 90],
            init_states=[[80, 30, 100]],
            random_seed=20,
            repeat_times=None,
            saturation_range=[30, 100],
            segment_length=None,
            segments=[0],
            sequence=None,
            spread=None,
            transition=0,
            transition_range=[2000, 6000],
            type="random",
        )

    @staticmethod
    def sunrise() -> "LightEffect":
        return LightEffect(
            id="TapoStrip_1OVSyXIsDxrt4j7OxyRvqi",
            name="Sunrise",
            brightness=100,
            display_colors=[[30, 0, 100], [30, 95, 100], [0, 100, 100]],
            enable=1,
            bAdjusted=None,
            brightness_range=[],
            backgrounds=[],
            custom=0,
            direction=1,
            duration=600,
            expansion_strategy=2,
            fadeoff=None,
            hue_range=None,
            init_states=[],
            random_seed=None,
            repeat_times=1,
            saturation_range=None,
            segment_length=None,
            segments=[0],
            sequence=[
                [0, 100, 5],
                [0, 100, 5],
                [10, 100, 6],
                [15, 100, 7],
                [20, 100, 8],
                [20, 100, 10],
                [30, 100, 12],
                [30, 95, 15],
                [30, 90, 20],
                [30, 80, 25],
                [30, 75, 30],
                [30, 70, 40],
                [30, 60, 50],
                [30, 50, 60],
                [30, 20, 70],
                [30, 0, 100],
            ],
            spread=1,
            transition=60000,
            transition_range=None,
            type="pulse",
            trans_sequence=[],
            run_time=0,
        )

    @staticmethod
    def sunset() -> "LightEffect":
        return LightEffect(
            id="TapoStrip_5NiN0Y8GAUD78p4neKk9EL",
            name="Sunset",
            brightness=100,
            display_colors=[[0, 100, 100], [30, 95, 100], [30, 0, 100]],
            enable=1,
            bAdjusted=None,
            brightness_range=[],
            backgrounds=[],
            custom=0,
            direction=1,
            duration=600,
            expansion_strategy=2,
            fadeoff=None,
            hue_range=None,
            init_states=[],
            random_seed=None,
            repeat_times=1,
            saturation_range=None,
            segment_length=None,
            segments=[0],
            sequence=[
                [30, 0, 100],
                [30, 20, 100],
                [30, 50, 99],
                [30, 60, 98],
                [30, 70, 97],
                [30, 75, 95],
                [30, 80, 93],
                [30, 90, 90],
                [30, 95, 85],
                [30, 100, 80],
                [20, 100, 70],
                [20, 100, 60],
                [15, 100, 50],
                [10, 100, 40],
                [0, 100, 30],
                [0, 100, 0],
            ],
            spread=1,
            transition=60000,
            transition_range=None,
            type="pulse",
            trans_sequence=[],
            run_time=0,
        )

    @staticmethod
    def valentines() -> "LightEffect":
        return LightEffect(
            id="TapoStrip_2q1Vio9sSjHmaC7JS9d30l",
            name="Valentines",
            brightness=100,
            display_colors=[
                [340, 20, 100],
                [20, 50, 100],
                [0, 100, 100],
                [340, 40, 100],
            ],
            enable=1,
            bAdjusted=None,
            brightness_range=[90, 100],
            backgrounds=[[340, 20, 50], [20, 50, 50], [0, 100, 50]],
            custom=0,
            direction=None,
            duration=600,
            expansion_strategy=1,
            fadeoff=3000,
            hue_range=[340, 340],
            init_states=[[340, 30, 100]],
            random_seed=100,
            repeat_times=None,
            saturation_range=[30, 40],
            segment_length=None,
            segments=[0],
            sequence=None,
            spread=None,
            transition=2000,
            transition_range=None,
            type="random",
            trans_sequence=None,
            run_time=None,
        )
