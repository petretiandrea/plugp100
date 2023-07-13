import enum
from typing import Optional

from plugp100.api.light_effect import LightEffect


class LightEffectPreset(enum.Enum):
    BubblingCauldron = 'Bubbling Cauldron'
    Aurora = 'Aurora'
    CandyCane = 'CandyCane'
    Christmas = 'Christmas'
    Flicker = 'Flicker'
    ChristmasLight = 'Grandma\'s Christmas Lights'
    Hanukkah = 'Hanukkah'
    HauntedMansion = 'Haunted Mansion'
    Icicle = 'Icicle'
    Lightning = 'Lightning'
    Ocean = 'Ocean'
    Rainbow = 'Rainbow'
    Raindrop = 'Raindrop'
    Spring = 'Spring'
    Sunrise = 'Sunrise'
    Sunset = 'Sunset'
    Valentines = 'Valentines'

    @staticmethod
    def from_name(name: str) -> Optional['LightEffectPreset']:
        return next([member for member in LightEffectPreset if member.value.lower() == name.lower()], None)

    def to_effect(self) -> LightEffect:
        _preset_mapping = {
            LightEffectPreset.BubblingCauldron: LightEffect.bubbling_calderon,
            LightEffectPreset.Aurora: LightEffect.aurora,
            LightEffectPreset.CandyCane: LightEffect.candy_cane,
            LightEffectPreset.Christmas: LightEffect.christmas,
            LightEffectPreset.Flicker: LightEffect.flicker,
            LightEffectPreset.ChristmasLight: LightEffect.christmas_light,
            LightEffectPreset.Hanukkah: LightEffect.hanukkah,
            LightEffectPreset.HauntedMansion: LightEffect.haunted_mansion,
            LightEffectPreset.Icicle: LightEffect.icicle,
            LightEffectPreset.Lightning: LightEffect.lightning,
            LightEffectPreset.Ocean: LightEffect.ocean,
            LightEffectPreset.Rainbow: LightEffect.rainbow,
            LightEffectPreset.Raindrop: LightEffect.raindrop,
            LightEffectPreset.Spring: LightEffect.spring,
            LightEffectPreset.Sunrise: LightEffect.sunrise,
            LightEffectPreset.Sunset: LightEffect.sunset,
            LightEffectPreset.Valentines: LightEffect.valentines,
        }
        return _preset_mapping[self]()
