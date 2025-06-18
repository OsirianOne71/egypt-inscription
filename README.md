# egypt-inscription
Creates a chisled sandstone image of hieroglyphics atring, virtically or horizontally, and inscribes the glyph characters you either paste directly or a string of Unicode Hex or combination of; then renders the final as a PNG image with. name you chose, automatically scaled to fit your characters.

Input Examples This Will Handle
- Mixed input       → `𓏙𓋹𓎃 132BD`   output  → `['𓏙', '𓋹', '𓎃', '𓊽']`
- Unicode hex only  → `130FB 131CB` output →  `𓃀𓂋`
- Glyph only        → `𓃀𓂋𓈖`       output →  `𓃀𓂋`


Next Branch - will allow you to render the character string surrounded by a shen   "I e. cartouche" if it's a name.

Possible edition: create a API call to an Phonetic name converter to heiroglyphs, and capture that string to auto insert into the shen.
