const { chromium } = require("playwright");

(async () => {
  // Launch browser with slowMo for throttling
  const browser = await chromium.launch({ headless: false, slowMo: 1000 });
  const context = await browser.newContext();
  const page = await context.newPage();

  try {
    // Navigate to the application
    console.log("Navigating to http://localhost:5173/");
    await page.goto("http://localhost:5173/");
    await page.waitForLoadState("networkidle");

    // Login process
    console.log("Starting login process...");
    // Fill email field
    await page.fill("#email", "admin@owi.com");
    // Fill password field
    await page.fill("#password", "admin");
    // Click login button
    await page.click("form > button");
    await page.waitForLoadState("networkidle");

    console.log("Login completed");
    // Set viewport
    // await page.setViewportSize({ width: 645, height: 1042 });

    // navigate to http://localhost:5173/assistants?view=create
    await page.goto("http://localhost:5173/assistants?view=create");
    await page.waitForLoadState("networkidle");

    // Click "Create Assistant" button
    console.log("Clicking Create Assistant...");
    await page.getByRole("button", { name: "Create Assistant" }).click();
    await page.waitForLoadState("networkidle");

    // Fill Assistant Name
    console.log("Filling assistant name...");
    await page.fill("#assistant-name", "asistente_ikasiker");
    // Fill Description
    console.log("Filling description...");
    await page.fill(
      "#assistant-description",
      "Eres un asistente experto en responder a preguntas de la convocatoria Ikasiker\n"
    );
    // Fill System Prompt
    console.log("Filling system prompt...");
    await page.fill(
      "#system-prompt",
      "Eres un asistente experto en responder a preguntas de la convocatoria Ikasiker\n"
    );
    // Fill Prompt Template
    console.log("Filling prompt template...");
    await page.fill(
      "#prompt_template",
      "Eres un asistente experto en respondes a preguntas de la convocatoria Ikasiker usando la técnica RAG (Retrieval-Augmented Generation).\nEsta es la pregunta o mensaje del usuario: {user_input}\nEste es el contexto: {context}\nAhora responde a la pregunta:"
    );
    // Fill Language Model (LLM)
    console.log("Setting language model...");
    await page.selectOption("#llm", { value: "gpt-5-mini" });
    // Fill RAG Processor
    console.log("Setting RAG processor...");
    await page.selectOption("#rag-processor", { value: "simple_rag" });
    // Save the assistant
    console.log("Saving assistant...");
    await page.getByRole("button", { name: "Save" }).click();
    await page.waitForLoadState("networkidle");

    console.log("Assistant creation completed successfully!");
    // await 5 seconds to observe the result
    await page.waitForTimeout(5000);
  } catch (error) {
    console.error("Error during automation:", error);
  } finally {
    // Keep browser open for debugging
    await browser.close();
  }
})();
