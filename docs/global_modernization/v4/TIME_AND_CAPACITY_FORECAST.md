# Оценка времени и capacity

## Базовые допущения

- один основной implementation lane;
- максимум два lane после стабилизации M03;
- один high-risk runtime owner migration на ветку;
- Cocos `3.8.8` без upgrade;
- Android QA только в emulator;
- runtime patch всегда получает свежий P4;
- owner/external waiting не входит в engineering effort.

## Прогноз

| Фаза | Engineering effort |
|---|---:|
| TC-01 + остаток operational preparation | 0.5–1.5 недели |
| M03 | 5–9 недель |
| M04 + M06 + M05 | 10–17 недель |
| M07 + M08 + M09 | 8–14 недель |
| M10 | 4–7 недель |
| M02/M12 closure | 3–6 недель + ожидание решений |
| Обязательный остаток | **31–55 engineer-weeks** |

Один последовательный lane: ориентировочно **8–13 календарных месяцев**. После M03 два аккуратно разделённых lane могут сократить календарный срок примерно до **6–10 месяцев**, но RC, интеграционные gates и cleanup остаются последовательными.

## Условный scope

- M11 PCG/DDA: `+8–14 engineer-weeks`.
- Google Play/AAB: примерно `+1–2 недели`, только после approval.
- Physical-device performance: примерно `+2–5 дней`, только после отдельной команды и при наличии стабильного RC.

## Диапазон, а не обещание

Наибольшая неопределённость — число фактических atlas families, визуальных recovery loops, save migration edge cases и release/signing waiting. После M03.7 и M04-A оценка должна быть пересчитана по измеренному inventory.

