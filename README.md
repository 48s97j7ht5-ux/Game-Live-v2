# Game Live v2

Станок персонажа в GitHub Actions: с телефона можно посчитать кадр и получить PNG.

## Как запустить с телефона

1. Открой репозиторий в приложении GitHub, ветка `cursor/character-factory-v0-a4d4`.
2. **Actions** → **Render character** → **Run workflow**.
3. Дождись зелёной галочки.
4. Смотри свежий кадр: `factory/out/front.png` (не кэшированный `character.png`).

Сейчас в станке не болванка, а готовая человеческая модель Michelle (Mixamo / three.js), рост ~200 px, до 48 цветов, камера спереди. Если снова спина — в Run workflow поставь yaw `0` или `180`.
