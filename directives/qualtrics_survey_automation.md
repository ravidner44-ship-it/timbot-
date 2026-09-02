# Qualtrics / Tell Tims Survey Automation SOP

## Objective
Automate the completion of Tell Tims (Tim Hortons / Restaurant Brands International) Qualtrics customer feedback surveys using receipt codes to retrieve coupon validation codes.

## Flow & Architecture
1. **Initialize Session**:
   - Make a GET request to `https://rbixm.qualtrics.com/jfe/form/SV_3lMYn8fpUtkEu7c?CountryCode=CAN&InviteType=Coupon&SC=21` with browser User-Agent headers.
   - Extract `appData` / `__jfefeRenderDocument`, retrieving `FormSessionID`, `XSRFToken`, `SurveyID`, `BrandDataCenterURL`, `JFEVersionID`, `SurveyVersionID`, and `RuntimePayload`.

2. **Dynamic Step Submission**:
   - Loop through active `QuestionIDs` returned in each step.
   - Construct payload according to `QuestionDefinitions` (`TE` Text Entry with receipt code `QID9`, `MC` Multiple Choice, `Matrix` ratings, `DB` Descriptive Blocks).
   - POST to `/jfe9/form/{SurveyID}/next` with incrementing `TransactionID` (`tid=1, 3, 5, ...`).

3. **End of Survey (EOS)**:
   - Detect `Messages.EOSMessage.FinalEOSMessage` in the response.
   - Regex extract `Validation Code: ([A-Z0-9]+)`.
   - Output validation code and save receipt log in `.tmp/`.

## Error Handling & Edge Cases
- **Invalid/Expired Receipt Code**: Detect early exit / validation failure.
- **Akamai Bot Protection**: Keep headers, cookies, and natural delays between question transitions.
- **Dynamic Branching**: Ensure universal question response builder handles unanticipated question types gracefully.
