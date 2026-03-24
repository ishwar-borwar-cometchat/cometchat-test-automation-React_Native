# Send Message, Single Line Composer & Rich Media Formatting

📥 [Download SM_SLC_RMF_Test_Cases.xlsx](https://github.com/ishwar-borwar-cometchat/cometchat-test-automation-React_Native/raw/main/Cometchat_Features/Send_%26_Compose/SM_SLC_RMF_Test_Cases.xlsx)

## Sheets

| Sheet | TCs | Description |
|-------|-----|-------------|
| Positive | 132 | Send message, emoji/sticker, @mention, composer features, rich media formatting |
| Negative | 22 | Empty/whitespace, injection attacks, voice recording edge cases |
| App Crash | — | Crash log with device, build, timestamp, severity |

## Execution Summary (Positive)

| Status | Count |
|--------|-------|
| PASS | 100 |
| FAIL | 14 |
| SKIP | 18 |

## Execution Summary (Negative)

| Status | Count |
|--------|-------|
| PASS | 7 |
| SKIP | 7 |
| Not Executed | 8 |

## Test Sections

| Section | IDs | Description |
|---------|-----|-------------|
| Send Message | MSG_001–MSG_031 | Input field, send, alignment, timestamps, scroll |
| Edit/Delete/Reply/Copy | MSG_032–MSG_040 | Long press actions |
| Reaction/Thread/Forward/Info | MSG_041–MSG_052 | Emoji reactions, threads, forwarding |
| i18n & Chronological | MSG_053–MSG_064 | Chinese, Arabic, Japanese, Hindi, mixed content |
| Emoji & Sticker | MSG_065–MSG_096 | Emoji input, sticker picker, categories |
| @Mention | MSG_097–MSG_110 | @all, member suggestions, group vs direct |
| Composer Features | MSG_111–MSG_121 | Draft, focus, link preview, paste, accessibility |
| Rich Media Formatting | MSG_122–MSG_132 | Bold, italic, underline, strikethrough, lists, code |
