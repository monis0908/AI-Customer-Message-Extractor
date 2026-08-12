# Short demonstration

Start the application:

```powershell
streamlit run app.py
```

1. Choose **Complete request**, then select **Extract**. Confirm all business
   fields are present and the JSON is shown.
2. Choose **Incomplete request**, then select **Extract**. Confirm the missing
   customer name, quantity, location, and deadline are visibly listed.
3. Choose **Contradiction**, then select **Extract**. Confirm `location` is
   `null` and a contradiction warning is displayed.
4. Replace the message with `What is the capital of France?`, then select
   **Extract**. Confirm the app marks it irrelevant.
5. Under **Review and correct this extraction**, edit a field if needed, choose
   whether the original prediction was correct, and select **Validate and save
   correction**. The app validates it before saving a local JSON Lines record.

The demo's only live API actions are the four **Extract** clicks. The correction
flow does not send a new Gemini request.
