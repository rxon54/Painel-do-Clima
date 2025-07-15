## Flexible Narrative Reconstruction for Painel do Clima (Refined)

The `curitiba-climate-infographic.html` mockup, while visually specific, conveys a clear narrative structure designed to inform and engage users about local climate change. The core idea is to translate complex climate data into understandable, actionable insights, following a logical flow from problem to solution.

### Main Narrative Components Extracted from Mockup:

1.  **Introduction & Context Setting:**
    *   **Purpose:** Briefly introduce the topic (climate change in a specific city) and set the stage for the information to follow.
    *   **Key Elements:** City-specific title, subtitle, and a high-level explanation of a core concept (e.g., "Climate Impact Index").
    *   **Data Points:** Current and projected overall climate risk index values.

2.  **Problem Statement & Quantification (Current vs. Future):**
    *   **Purpose:** Visually and numerically illustrate the change in climate risk over time.
    *   **Key Elements:** Comparison of a key metric (e.g., overall risk index) between a baseline (today) and a future projection (e.g., 2050).
    *   **Data Points:** Numeric values for current and future states, qualitative labels (e.g., "Risco Médio", "Risco Alto").

3.  **Drivers of Risk (Why is it Changing?):**
    *   **Purpose:** Explain the underlying factors contributing to the climate risk.
    *   **Key Elements:** Categorization of risk into components (e.g., Exposure, Sensitivity, Adaptation Capacity), each with a definition and local context/example.
    *   **Data Points:** Scores or indices for each risk driver, and their qualitative interpretation.

4.  **Specific Impacts (What will Happen?):**
    *   **Purpose:** Detail concrete, localized climate impacts that are projected to occur.
    *   **Key Elements:** Specific climate phenomena (e.g., heavy storms, dry days, heat), their projected change (e.g., quantitative delta or before/after values), and a simple explanation of the consequence.
    *   **Data Points:** Current and projected values for specific climate indicators, units, and concise descriptions of their real-world effects.

5.  **Daily Life Implications (How does it Affect Me?):**
    *   **Purpose:** Translate the specific impacts into tangible, relatable scenarios for citizens.
    *   **Key Elements:** Short, impactful phrases describing everyday consequences (e.g., "Picos de água", "Vales de água", "Ilha de calor").
    *   **Data Points:** Qualitative descriptions of daily life impacts.

6.  **Solutions & Preparation (How Can We Prepare?):**
    *   **Purpose:** Offer actionable strategies and positive outlooks for adaptation and mitigation.
    *   **Key Elements:** Categories of solutions (e.g., Green City, Water Management, Community Care), each with a brief explanation of the approach.
    *   **Data Points:** High-level solution themes and their associated descriptions.

7.  **Concluding Message:**
    *   **Purpose:** Reinforce a positive or empowering message.
    *   **Key Elements:** A final message that encourages action or provides hope.

### Main Idea Behind the Mockup:

The core idea is to create a compelling, localized narrative that moves from:

*   **Problem Identification (Today vs. Future):** Highlighting the urgency and scale of climate change at a local level.
*   **Causality (Why):** Explaining the contributing factors in an accessible way.
*   **Specific Manifestations (What):** Detailing concrete impacts that resonate with local experiences.
*   **Personal Relevance (How it Affects Daily Life):** Making the abstract impacts tangible.
*   **Empowerment & Action (Solutions):** Providing actionable steps and fostering a sense of agency and hope.

This flow is designed to educate, raise awareness, and motivate action by presenting complex scientific data in a digestible and emotionally resonant manner.

### Flexible Pathway to Reconstruct Narratives (Refined):

Instead of directly reconstructing the HTML mockup, we will focus on generating the *content* for each narrative component in a structured, format-agnostic way. This allows for greater flexibility in how these narratives are consumed (e.g., web infographics, text summaries, audio bulletins, social media posts, LLM agent context).

Here's a proposed flexible pathway:

1.  **Define a Structured Data Model for Narrative Components:**
    *   For each narrative component identified above (Introduction, Problem Statement, Drivers, Impacts, Implications, Solutions, Conclusion), define a JSON schema or similar structured format.
    *   This schema would specify the required fields (e.g., `title`, `body_text`, `icon`, `value_current`, `value_projected`, `unit`, `examples`, `action_items`).
    *   This ensures consistency in the information generated, regardless of the final output format.

2.  **Data Filtering and Pre-processing for LLM Input:**
    *   Before feeding data to the LLM, implement a filtering step to remove indicators that have 'good' or 'positive' grades. This will reduce the context load for the LLM and allow it to focus on problematic areas, as per user feedback.
    *   This pre-processing step will ensure that the LLM receives only the most relevant data for generating narratives about climate risks and impacts.

3.  **LLM-Driven Content Generation per Component:**
    *   Leverage powerful LLM models via API and Python SDK to generate the prose and specific details for each narrative component. The LLM will draw from the filtered raw climate data (from AdaptaBrasil) and the processed JSON files (e.g., `data/LLM/PR/5329/*.json`).
    *   **Target Audience & Tone:** The LLM will be prompted to generate content suitable for a broad audience, including newsrooms, the general public, and policymakers. The initial focus will be on a direct-access, engaging tone for the 'landing page' type content, similar to the mockup, but without emojis for now.
    *   **Prompt Engineering:** Prompts will be carefully crafted to guide the LLM in maintaining the desired tone, level of detail, and use of relatable analogies. Emojis will not be explicitly requested from the LLM at this stage, as human review will handle content polishing.
    *   **Example for "Problem Statement & Quantification":**
        *   **Input to LLM:** City name (Curitiba), current overall risk index (0.35), projected 2050 risk index (0.55), context about the "Climate Impact Index" (0-1 scale, higher is worse), and filtered problematic indicators.
        *   **LLM Output (JSON/Structured Text):**
            ```json
            {
              "component_type": "problem_statement",
              "title": "Curitiba: Risco Climático Hoje vs. 2050",
              "current_value": 0.35,
              "current_label": "Risco Médio",
              "projected_value": 0.55,
              "projected_label": "Risco Alto!",
              "explanation": "Imagine uma nota de 0 a 1 que mede o quanto nossa cidade sofre com as mudanças do clima. É como um termômetro do problema: quanto mais alto, mais preocupante! Curitiba tem nota 0,35 hoje (médio), mas em 2050 pode chegar a 0,55 - isso é quase o dobro de problemas climáticos!"
            }
            ```
    *   The LLM will focus on generating the textual content, and human-in-the-loop review by specialized journalists will be a critical step for polishing the content, including the addition of emojis and further tailoring for specific audiences if needed.

4.  **Dynamic Assembly and Rendering:**
    *   Once each narrative component's content is generated in a structured format, these components can be assembled dynamically.
    *   **Flexible Rendering:** Different rendering modules could consume this structured data to produce:
        *   **HTML Infographics:** Using a more abstract HTML template that iterates through the structured components.
        *   **Plain Text Summaries:** For reports or quick overviews.
        *   **Audio Script:** For text-to-speech generation (e.g., for audio bulletins).
        *   **Social Media Snippets:** Extracting key facts and calls to action.
        *   **LLM Context:** Directly feeding the structured narrative components to other LLMs for further analysis or conversational interfaces.

5.  **Integration with Existing Pipeline:**
    *   A new script (e.g., `backend/generate_narratives.py`) would orchestrate the LLM calls, taking the city ID and relevant filtered JSON data as input.
    *   This script would output the structured narrative components into a new set of JSON files (e.g., `data/LLM/<STATE>/<CITY_ID>/narratives.json`).
    *   Downstream processes (e.g., `generate_html_infographic.py`, `generate_audio_bulletin.py`) would then consume these `narratives.json` files.

6.  **Human-in-the-Loop Review and Refinement:**
    *   Specialized journalists will review and polish the LLM-generated narratives. This includes ensuring accuracy, clarity, tone, and adding elements like emojis or specific calls to action for different target groups (e.g., 'I am a concerned citizen, how can I help?', 'I am a policymaker, how can I help?').
    *   This step ensures the final output is high-quality and meets the project's communication objectives.

This refined approach provides a robust and flexible framework for generating localized climate narratives, leveraging LLM capabilities while incorporating essential human oversight and adaptability for various output formats and audiences.



### 2. Data Filtering and Pre-processing for LLM Input (Detailed)

To ensure the LLM focuses on problematic areas and to reduce context load, a crucial pre-processing step will be implemented. This involves filtering out indicators that are currently in a 'good' or 'positive' state based on their numerical value and the `proporcao_direta` field.

**Understanding `proporcao_direta`:**

*   `"proporcao_direta": "1"`: For indicators with this value, a **higher numerical value indicates a worse situation**. Therefore, a **low numerical value** signifies a 'good' or 'positive' grade.
*   `"proporcao_direta": "0"`: For indicators with this value, a **higher numerical value indicates a better situation**. Therefore, a **high numerical value** signifies a 'good' or 'positive' grade.

**Filtering Logic:**

An indicator will be considered 'good' and filtered out if it meets the criteria for a positive state based on its `value` and `proporcao_direta`. Additionally, the `valuecolor` field can serve as a secondary confirmation, as certain colors (e.g., green shades like `#A9DE00`, `#02C650`) are consistently used to denote positive conditions within the AdaptaBrasil data.

**Specific Implementation:**

1.  **Thresholds:** Define appropriate numerical thresholds for 'good' values for both `proporcao_direta` cases. These thresholds will be determined based on analysis of the data ranges and the associated `rangelabel` values (e.g., 'Baixo', 'Muito baixo' for `proporcao_direta=1`, and 'Alto', 'Muito alto' for `proporcao_direta=0`).
2.  **Color Codes:** Maintain a list of `valuecolor` codes that explicitly represent 'good' conditions.
3.  **Filtering Function:** A function will be developed to evaluate each indicator. If an indicator's current `value` (and potentially its `valuecolor`) falls within the 'good' criteria based on its `proporcao_direta`, it will be excluded from the data passed to the LLM.

This targeted filtering ensures that the LLM's input is streamlined to highlight only the areas of concern, allowing for more focused and relevant narrative generation about climate risks and impacts.



### 3. LLM Prompting Strategy and Content Generation

With the filtered problematic indicators, the next step involves leveraging LLMs to generate narrative components. The strategy focuses on creating distinct prompts for each desired narrative section, ensuring the LLM produces structured JSON output that aligns with our `NarrativeComponent` data model.

**Prompting Principles:**
*   **Role-Playing:** The LLM is instructed to act as an "expert climate communicator for the 'Painel do Clima' project," emphasizing clarity, engagement, and an informative tone for diverse audiences (general public, newsrooms, policymakers).
*   **Output Format:** Each prompt explicitly requests JSON output, defining the required keys and their expected data types. This ensures consistency and facilitates programmatic parsing.
*   **Language and Tone:** Instructions specify Brazilian Portuguese and a serious but empowering tone, balancing challenges with solutions.
*   **Contextualization:** Prompts provide relevant data (e.g., city name, risk indices, specific indicator data) to ground the LLM's generation in factual information.
*   **Constraint-Based Generation:** Negative constraints (e.g., "Avoid emojis for now") are included to guide the LLM's output.

**Narrative Components Generated by LLM:**
1.  **Introduction:** Introduces the city's climate change context and presents current and projected Climate Impact Index values.
2.  **Problem Statement:** Quantifies the climate problem, explaining the significance of the Climate Impact Index and its projected increase.
3.  **Risk Drivers:** For relevant problematic indicators (e.g., 'vulnerabilidade', 'capacidade adaptativa'), the LLM explains the indicator, its relevance, and current implications.
4.  **Specific Impacts:** For specific problematic indicators (e.g., 'seca', 'precipitação'), the LLM details the 'stat-change' and real-world implications for daily life.
5.  **Daily Life Implications:** Summarizes the overall daily life consequences based on all problematic indicators, presented as a list of short, impactful phrases.
6.  **Solutions:** Proposes high-level actionable solutions and preparation strategies based on problematic indicators, presented as themes with brief explanations.
7.  **Conclusion:** A positive and empowering concluding message encouraging action.

**Implementation Details (`backend/generate_narratives.py` and `backend/llm_prompts.py`):**
*   **`generate_llm_response(prompt)` function:** Handles interaction with the OpenAI API, sending the crafted prompts and attempting to parse the LLM's response into a JSON object. Robust error handling is included to manage potential `JSONDecodeError` and to extract JSON from markdown code blocks if the LLM wraps its output.
*   **`create_climate_narrative(city_id, city_name, problematic_indicators)` function:** Orchestrates the generation of the complete climate narrative. It iterates through the defined narrative components, calls the LLM with the appropriate prompt for each, and appends the generated `NarrativeComponent` objects to a list. Placeholder values for `current_risk` and `projected_risk` are used for demonstration, but in a production environment, these would be dynamically calculated.
*   **`backend/llm_prompts.py`:** Contains functions for each narrative component, dynamically constructing the prompts with relevant data. This modular approach allows for easy modification and expansion of narrative sections.

This structured prompting approach ensures that the LLM generates consistent, relevant, and parsable content for each part of the climate narrative, laying the groundwork for flexible rendering into various output formats.



### 4. Flexible Rendering Modules

To ensure the narratives can be consumed in various formats, a flexible rendering module has been implemented. This module takes the structured JSON output from the LLM and transforms it into a human-readable format. Initially, an HTML renderer (`backend/render_html.py`) has been developed using Jinja2 templating. This allows for easy customization of the visual presentation without altering the core narrative generation logic.

**Implementation Details:**
- **`backend/render_html.py`**: Contains the `render_narrative_to_html` function responsible for loading the `climate_narrative.json` and rendering it into an HTML file using a Jinja2 template.
- **`templates/narrative_template.html`**: A basic HTML template is provided to structure the narrative components. This template can be easily modified or replaced to generate different visual layouts or even other text-based formats (e.g., Markdown, plain text) by creating new rendering functions and templates.
- **Integration with `generate_narratives.py`**: After the `climate_narrative.json` is generated, the `render_narrative_to_html` function is called to produce the HTML output, saving it to `data/LLM_processed/<state>/<city_id>/climate_narrative.html`.

This modular approach ensures that as new output formats are required (e.g., PDF, presentation slides, direct API endpoints), new rendering modules can be developed and integrated without impacting the data processing or LLM interaction layers.




### 5. Overall Process Flow and Integration

The entire narrative generation process is orchestrated by the `generate_narratives.py` script. This script acts as the central hub, managing the flow from raw data input to the final rendered output.

**Process Steps:**

1.  **Data Loading and Filtering:**
    *   The `generate_narratives.py` script loads the sector-based JSON files for a given city (e.g., `data/LLM/PR/5329/*.json`).
    *   It then applies the `is_indicator_problematic` function to each indicator within these files. This function, based on the `proporcao_direta` and `value` fields, identifies indicators that are currently problematic or show a worsening trend.
    *   Only these problematic indicators are collected and passed on for LLM processing, significantly reducing the context size and focusing the narrative on areas of concern.

2.  **LLM-Driven Narrative Component Generation:**
    *   The `create_climate_narrative` function within `generate_narratives.py` takes the filtered problematic indicators as input.
    *   It iteratively calls the `generate_llm_response` function for each narrative component (Introduction, Problem Statement, Risk Drivers, Specific Impacts, Daily Life Implications, Solutions, Conclusion).
    *   Each call to `generate_llm_response` sends a carefully crafted prompt (from `llm_prompts.py`) to the LLM (currently `gemini-2.5-flash`). The LLM is instructed to return its response in a structured JSON format, which is then parsed and validated against the `NarrativeComponent` Pydantic model (defined in `narrative_models.py`).
    *   The generated components are collected into a `ClimateNarrative` object.

3.  **Structured JSON Output:**
    *   Once all narrative components are generated, the complete `ClimateNarrative` object is saved as a structured JSON file (e.g., `data/LLM_processed/PR/5329/climate_narrative.json`). This JSON file serves as the canonical, format-agnostic representation of the climate narrative.

4.  **Flexible HTML Rendering:**
    *   Immediately after generating the JSON narrative, the `render_narrative_to_html` function (from `render_html.py`) is invoked.
    *   This function takes the `ClimateNarrative` object and a specified output path, and uses a Jinja2 template (`templates/narrative_template.html`) to render the narrative into a human-readable HTML file (e.g., `data/LLM_processed/PR/5329/climate_narrative.html`).

**Automation Hooks:**

*   The `generate_narratives.py` script is designed to be run from the command line, accepting `city_id`, `state_abbr`, `input_data_dir`, and `output_data_dir` as arguments. This makes it easy to integrate into existing data pipelines or scheduled tasks.
*   For example, it can be triggered by a `cron` job or as part of a larger data processing workflow. The output HTML can then be served directly or further processed for other platforms.

**Validation and Edge Cases:**

*   **Missing Data:** The `is_indicator_problematic` function handles cases where `current_value` is `None`, marking such indicators as problematic to ensure they are reviewed.
*   **LLM Response Robustness:** The `generate_llm_response` function includes error handling for JSON parsing, attempting to extract JSON from markdown code blocks if direct parsing fails. This makes the system more resilient to variations in LLM output.
*   **Pydantic Models:** The use of Pydantic models (`NarrativeComponent`, `ClimateNarrative`) provides schema validation, ensuring that the generated JSON adheres to the expected structure. This helps catch issues early in the process.
*   **Human-in-the-Loop:** As discussed, the final and most critical validation step involves human review by specialized journalists. This ensures the accuracy, tone, and overall quality of the generated narratives before publication. This human oversight can also address any edge cases or nuances that automated processes might miss.

This integrated approach provides a robust, flexible, and scalable solution for generating dynamic climate narratives, with clear stages for data processing, LLM interaction, and multi-format rendering.

