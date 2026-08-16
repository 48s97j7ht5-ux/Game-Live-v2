# Game Live v2

Веб-станок болванки: https://48s97j7ht5-ux.github.io/Game-Live-v2/

Болванка — MakeHuman hm08 (глина), CC0, морфы груди/живота/бёдер/попы.

На телефоне можно крутить объёмное тело пальцем. Кнопки: анфас, ¾, профиль, спина.

Пиксельный кадр по-прежнему считается в **Actions → Render character** и лежит в `factory/out/front.png`.

Если страница 404 — в GitHub: Settings → Pages → Source: GitHub Actions.

Станок персонажа в GitHub Actions: с телефона можно посчитать кадр и получить PNG.

## Как запустить с телефона

1. Открой репозиторий в приложении GitHub, ветка `cursor/character-factory-v0-a4d4`.
2. **Actions** → **Render character** → **Run workflow**.
3. Дождись зелёной галочки.
4. Смотри свежий кадр: `factory/out/front.png` (не кэшированный `character.png`).

Сейчас в станке **объёмная телесная болванка** MakeHuman/MPFB (без одежды и причёски), рост ~200 px, камера спереди. Кадр: `factory/out/front.png`. Если спина — в Run workflow поставь yaw `90` или `180`.

