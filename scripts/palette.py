# LOCKED palette — Game Boy "Colorswall #171284" sheet + 000BC4 (virtual add).
# Every panel/element color MUST come from here.
PALETTE = {
  # Fireball Red
  "fireball_red":"#D31E25", "repos_red":"#94151A", "red_540C0F":"#540C0F", "red_150304":"#150304",
  # Curry Gold
  "curry_gold":"#D7A32E", "gold_977220":"#977220", "gold_564112":"#564112", "gold_151005":"#151005",
  # Indian Pale Ale
  "ipa_D1C02B":"#D1C02B", "ipa_92861E":"#92861E", "ipa_544D11":"#544D11", "ipa_151304":"#151304",
  # Classic Green
  "classic_green":"#369E4B", "green_266F35":"#266F35", "green_163F1E":"#163F1E", "green_051007":"#051007",
  # Aqueduct Cyan
  "aqueduct_cyan":"#5DB5B7", "cyan_417F80":"#417F80", "cyan_254849":"#254849", "cyan_091212":"#091212",
  # Forbidden Blackberry
  "blackberry":"#31407B", "bb_222D56":"#222D56", "bb_141A31":"#141A31", "bb_05060C":"#05060C",
  # Putnam Plum
  "putnam_plum":"#803F64", "plum_612C46":"#612C46", "plum_371928":"#371928", "plum_0E060A":"#0E060A",
  # Fig Maroon
  "fig_maroon":"#4F2E39", "maroon_37202S":"#372028", "maroon_201217":"#201217", "maroon_0S0506":"#080506",
  # virtual add (only non-sheet color, per user)
  "credentials_blue":"#000BC4",
  # plain white/black used for text & pixel marks
  "white":"#FFFFFF", "black":"#000000",
}
# canonical roles seen in the mockup
PANEL_SHADOW = PALETTE["putnam_plum"]   # every panel drop-shadow
PANELS = {
  "header":   PALETTE["aqueduct_cyan"],
  "wheel":    PALETTE["blackberry"],
  "repos":    PALETTE["repos_red"],
  "radar":    PALETTE["curry_gold"],
  "moreme":   PALETTE["ipa_D1C02B"],
  "progress": PALETTE["fig_maroon"],
}

# ---- bevel ramps (tints/shades) extracted from mega.svg ----
# Plum 803F64 frame bevel ramp:
PLUM_LIGHT = "#ac829a"   # highlight (top+left of border)
PLUM_DARK  = "#4c253c"   # shadow    (bottom+right of border)
PLUM_DEEP  = "#391c2c"   # deep drop-shadow (offset)
PLUM_MID2  = "#9c5b79"   # extra mid tint
# generic dark page shadow used inside cards
CARD_SHADOW = "#000000"
