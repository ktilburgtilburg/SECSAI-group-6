SECSAI
Real-Time URL Threat Detection
Final Report
Software Engineering for CSAI - Group 6
Erik Hriňa, Filip Šarík, Jarod Rodriguez, Koen van Tilburg, Alexander Lee
https://github.com/ktilburgtilburg/SECSAI-group-6

 Contents
1. Problem Definition, Objectives and KPIs	3
1.1 Problem definition	3
1.2 Objectives	3
1.3 Measurements / KPIs	4
2. From Data to AI	4
2.1 Data collection	4
Why these features	5
2.2 Model	6
2.3 Software	6
3. Software Requirements Specification	7
3.1 Introduction	7
3.2 User requirements	7
3.3 Functional requirements	8
3.4 Non-functional requirements	9
3.5 AI-specific requirements	9
3.6 Requirement status	10
4. Project Management and Implementation	11
5. Implementation and Testing	11
5.1 Unit tests	11
5.2 Component and integration tests	12
5.3 Implementation progress	13
6. Task 6 - Distributed Architecture	13
7. Task 7 - Wrapping Up	15
7.1 Final state of the system	15
7.2 Value Sensitive Design	15
7.3 Environmental impact	16
7.4 Teamwork	16
Sources	16


 1. Problem Definition, Objectives and KPIs
1.1 Problem definition
The web is now part of daily life: we use it to work, study, shop, bank and read the news. That same reach makes it a target for attackers, who lure users to phishing pages, malware downloads and defaced sites, often through a link in an email, chat message or social media post.
This affects a layered set of groups: the organisations that would deploy a detection tool (IT and security staff at companies with strict data-handling rules), and, ultimately, the staff whose safety the system exists to protect. This last group matters most, since they are often the least prepared to recognise a well-made malicious link. We are a small development team building this product for such client organisations.
Left unaddressed, the damage is real, including financial loss, stolen identities, infected devices, emotional harm, and a wider decline of trust in online services, consequences that fall hardest on the very people least equipped to spot the warning signs.
The main challenge is that a malicious link is hard to judge by eye. Attackers use look-alike domains (paypa1.com), long URLs that push the real host out of view, raw IP addresses and randomly generated names, and they change these tricks quickly. Blacklists only catch links that are already known. Any warning also risks flagging honest sites by mistake, so the system has to explain why it raised a flag and leave the final decision to the user. In short, the problem is to detect malicious URLs before the page opens and explain why they were flagged, doing so accurately, adaptably to new attack patterns, in a privacy-friendly way, and light enough to run at a small scale.
The goal is a small-scale detection system that runs inside the client organisation's own network. It breaks down along two axes: the steps of a check (intercepting a link in the browser, assessing it, and showing the verdict) and the threat types it must recognise (phishing, malware and defacement).
Proposed solution. A browser add-on that checks every link the user opens. Input: the URL. Output: a verdict (safe or malicious), a confidence level and the main reasons, shown as a warning the user can act on.
1.2 Objectives
We use a four-level hierarchy. Each objective is split into sub-objectives, and every sub-objective has a KPI in Section 1.3.
Organisational (O1) - The system should be efficient (O1.1), small-scale and scalable (O1.2). We should be able to scale the system post-deployment in the number of users and in the threats it detects. The project can be considered a success when the system is deployed and actively used by a client organisation (O1.3).
Leading (O2) - The deployed system's success can be measured by how reliably it protects users. When a user opens a link, the verdict should be accurate (O2.1) and the service should be available (O2.2). The system should be able to be relied on by users with less security awareness.
User-oriented (O3) - For the users it is important that the system misses as few malicious links as possible without flooding them with false alarms (O3.1). A false negative could mean that the user suffers financial losses. When the user opens a link, the system should check it automatically and return a verdict within 3 seconds (O3.2), with no extra steps for the user (O3.3). In case of a wrong verdict, the user should be provided with an easy way to override and report it (O3.4). This will make the user experience as seamless as possible.
Component (model) (O4) - The AI model should classify a URL from the URL alone. The model performance will be optimal when it can deliver a timely (O4.2) and accurate (O4.1) response with clear classification and a concise explanation of why the URL was flagged (O4.3).
1.3 Measurements / KPIs
Precision is the percentage of flagged URLs that are actually malicious. Recall is the percentage of all malicious URLs that the system catches. We prioritise recall over precision, as false negatives can be more harmful than false positives.
Objective	KPI (what exactly is measured)	Target
O1.1 Efficient	Compute per check: CPU time per prediction, and whether the whole system runs on one standard laptop	≤ 50 ms CPU per prediction; runs on one laptop
O1.2 Scalable	Throughput (requests per second) in a load test of 500 requests with 1 worker and with 3 workers	Throughput rises as workers are added
O1.3 Adopted	Weekly active devices ÷ devices with the extension installed at the client organisation (replaces monthly active users)	≥ 80% after the first month
O2.1 Accurate in use	False alarms on a fixed bank of well-known safe sites, and verdicts reported as wrong per 1,000 checks	0 false alarms on the bank; reports tracked
O2.2 Available	Share of checks that return a verdict instead of an error, from the request log	≥ 99%
O3.1 Few misses, few false alarms	Miss rate (malicious test URLs classified as benign) and false-alarm rate (benign test URLs flagged)	Miss rate ≤ 15%; false-alarm rate ≤ 2%
O3.2 Fast	Time from opening a link to the verdict (95th percentile)	≤ 3 s
O3.3 Easy to use	Steps to install; clicks needed to act on a warning; System Usability Scale (SUS) score from a short user test (replaces the satisfaction rate)	≤ 5 steps; 1 click; SUS ≥ 70
O3.4 User in control	Share of warnings overridden with "Proceed Anyway" (a high rate signals false alarms or warning fatigue)	< 20%, otherwise review
O4.1 Accurate model	Recall on the malicious class and macro-F1 on a held-out test set	Recall ≥ 0.85; macro-F1 ≥ 0.90
O4.2 Fast model	Inference time per URL	< 1 s (aim < 50 ms)
O4.3 Explainable	Share of malicious verdicts that come with at least one human-readable reason	100%

2. From Data to AI
2.1 Data collection
To solve the described problem, a dataset containing 651,191 URLs is used. The dataset has only 2 columns: URL and label. The label column contains four values: benign, defacement, phishing, and malware.
Label	Count	Percentage
benign	428,103	65.74%
defacement	96,457	14.81%
phishing	94,111	14.45%
malware	32,520	4.99%

•	Volume: The dataset contains 651,191 rows and is approximately 45.6 MB in size.
•	Velocity: The creators update this dataset once a year, although in a real-world setting URL traffic arrives continuously in real time.
•	Variety: There is high variety in how the URLs look, ranging from short domain names to long query paths, different top-level domains, and raw IP addresses instead of domain names.
•	Veracity: The dataset contains URLs from multiple academically accepted phishing databases which the authors simplified to only have URL and label columns, adding benign links for machine learning. During exploration, we found that veracity was mostly good with no missing values, but we discovered 10,072 duplicate URLs and 6 rows of label discrepancies where a duplicated link had conflicting labels. We dropped these duplicates and conflicting rows to keep the data clean and prevent data leakage.

The imbalance between benign and malicious URLs is quite large, with benign links making up around 66% of the dataset. For preprocessing, the raw link URL string cannot be fed directly into a machine learning model, so we parsed each URL using urllib.parse and tldextract to extract its scheme, hostname, registrable domain, subdomain, path, and query. Transport protocols (http/https) are stripped before feature extraction (see the note on the scheme shortcut below). The final model uses 27 handcrafted features.
Why these features
Each feature captures a trick attackers use to make a link look trustworthy or to avoid filters:
Feature	Why it helps
Lengths (total, hostname, path)	Phishing URLs are often long, to push the real domain out of view or bury a brand name deep in the path.
Character counts (dots, hyphens, slashes, digits, @, ?, =, underscores, special chars, digit ratio)	Many dots signal subdomain abuse (paypal.com.secure-login.xyz); hyphens are common in look-alikes (secure-paypal); an @ makes the browser ignore everything before it; many ? and = point to redirect or tracking parameters.
Structural flags (IP host, port, punycode)	Legitimate sites rarely use raw IP addresses or non-default ports. Punycode (xn--) signals homograph attacks.
Subdomain and query structure	Deep subdomains and many query parameters are common phishing patterns.
Sensitive words count	Credential-harvesting pages name the action they want the victim to take (login, verify, bank).
TLD risk	A scalar risk score that says how risky a domain's ending is. .gov = 0.05, .com = 0.10, .xyz = 0.70, .tk = 0.85. These values reflect the general pattern that some endings are heavily abused for phishing, while other TLDs like .gov or .edu are almost never. The model can't learn this from the dataset because most endings appear too rarely to draw conclusions from, so we provide it as a feature instead.
Brand impersonation (edit distance to nearest known brand, exact-brand flag, brand-in-subdomain flag, normalized edit distance)	Separate real brand domains (google.com, distance 0) from typosquats (go0gle.com, distance 1) and brand-in-subdomain attacks (google.com.evil.ru).

An earlier iteration also used a character-level TF-IDF n-gram matrix alongside these features. We removed it in the final model because it added complexity without meaningful accuracy gain.
2.2 Model
The model takes a raw URL string as input (e.g. br-icloud.com.br) and returns a verdict with a confidence score and a short list of possible explanations. The dataset is split 80/10/10 into train, validation, and test sets, stratified by label. The validation set is used for threshold selection; the test set is held out for the final evaluation. Class weights are set to "balanced" so that the minority class (malicious, ~33% of the data) is penalized more heavily during training.

Our first model was a four-class SGD classifier (benign/defacement/phishing/malware) using 19 handcrafted features plus a character-level TF-IDF n-gram matrix. [its metrics: 96.8% accuracy, 0.932 macro F1, 0.04 ms inference, 22s training]. We later found this accuracy was inflated by a data shortcut: 91.7% of benign URLs had no scheme while malicious URLs mostly did, so the model learned "scheme = malicious." We also found the first deployed model flagged almost every URL as malicious, including google.com.

The final model was rebuilt as a binary Random Forest (benign/malicious) with 27 handcrafted features and no TF-IDF. We rebuilt to binary rather than four-class because the deployment target is a warn/block extension that does not distinguish between malicious subclasses . The features were expanded with brand-impersonation signals (edit distance to known brands) and a TLD risk score; TF-IDF was removed because it added complexity without meaningful accuracy gain. The final model achieves a macro F1-score of 0.8636 on the held-out test set using a classification threshold of 0.55. At this threshold, the model achieves a malicious-class precision of 82.68% and recall of 80.48%, with a false positive rate (FPR) of 8.24%. The threshold was selected based on its macro F1-score, which was the highest among the evaluated thresholds.

Training takes approximately 3 minutes on a standard laptop CPU. Inference is 14.6 ms per URL on a warm model (mean over 1,000 samples), with 95% of requests completing within 22.5 ms and a cold start of ~2 seconds. The cold start is paid once when the worker process loads the model and is not incurred per request. The model file is 254 MB after capping depth and leaf size; an earlier uncapped configuration produced a 1.2 GB file and 37 ms inference.
2.3 Software
All the model work was done in Python. We used Jupyter Notebook to explore the data, build features, and test the model as we went. The dataset was loaded and handled with pandas and NumPy.
To prepare the data, we split each URL into its parts using tldextract and urllib.parse. Handcrafted features such as character counts, digit ratios, and edit distances are computed with Python's built-in tools (re, ipaddress) and python-Levenshtein for fast edit distance. tldextract also provides the TLD suffix used for the TLD-risk feature. 
The final model is a RandomForestClassifier, trained and evaluated entirely with scikit-learn (train_test_split, RandomForestClassifier, permutation_importance, classification_report, confusion_matrix). The scaler, model, and label classes are saved with joblib for deployment. Matplotlib and seaborn were used for visualizations.
The final product is a browser extension, built with HTML, CSS, and JavaScript with a Manifest V3 file. To use the trained model inside it, the model is saved with joblib and served through a small Python backend (Flask), which the extension calls to get a verdict on a link. Later in the development process we split this backend into an interface server, a message queue (RabbitMQ) and separate model workers, all run with Docker Compose. For development, we used VS Code as the editor and Git with GitHub for version control and teamwork. Python dependencies are managed with uv.
3. Software Requirements Specification
3.1 Introduction
This Software Requirements Specification (SRS) describes the requirements for a machine-learning-based URL classification system developed as part of our university group project. The system analyses URLs and classifies them as benign or malicious, and provides a confidence score. This document defines the user, system, functional, non-functional, and AI-specific requirements of the system.
Purpose. We are a small development team building this product for client organisations with strict data-handling rules (see Section 1). The purpose of the project is to develop a lightweight browser extension that helps the client's staff identify potentially malicious URLs. A trained machine-learning model analyses a submitted URL and predicts its category. The system should prioritise detecting malicious URLs, since failing to identify a harmful URL is considered more serious than occasionally classifying a benign URL as malicious. It should display an output within 3 seconds and warn the user if a malicious link is detected.
Intended audience. This document is intended for the project team, the course instructors, and anyone involved in testing or evaluating the system. It provides a common reference for what the system should do and which requirements the final implementation should meet.
Additional information. Because the system uses machine learning, its predictions are not guaranteed to be correct. Its performance depends on the quality of the training data and may decrease as new types of malicious URLs appear. The model should therefore be evaluated carefully.
3.2 User requirements
ID	Requirement
UR1	The extension shall assess a URL before the user accesses its destination.
UR2	The system shall display whether the URL is potentially dangerous within 3 seconds of the user attempting to access the URL.
UR3	If a URL is assessed as potentially dangerous, the system shall display a warning containing the URL and a message stating that the URL is potentially dangerous, with options to either proceed to the URL or cancel the navigation.
UR4	If a URL is assessed as not potentially dangerous, the system shall proceed to the URL.
UR5	If the system is unable to assess the URL within 2 seconds, the system shall show that the URL could not be verified and shall not block the navigation.
UR6	The system shall allow the user to submit a report that the URL assessment was incorrect. Only the site's hostname and the shown and reported verdicts are stored.
UR7	If the user believes a warning is wrong, they shall be able to override it with one click and continue to the site. The site is then temporarily allowlisted so the warning does not repeat.

3.3 Functional requirements
ID	Feature	Description	Priority	Result
FR1	Extension	Users will have to install a browser extension to use the application.	High	A quick installation and use of the application in browsers known to the developers.
FR2	Browsers	The extension shall support the Chromium browsers.	High	Control over which browsers the system shall support.
FR3	Explanation	The system shall give the user a description of non-benign URLs. This will contain the main reasons for the verdict paired with a confidence score.	Low	This gives the user more insight into why the system marked a URL as malicious.
FR4	Warning screen	The system shall inform the user of dangerous URLs with a full-page warning in the current tab.	Med	Users will be able to choose to proceed to the following page or not.
FR5	Result	The system will give each URL a boolean classification with a confidence score. The URL will either be malicious or non-malicious.	High	This will make it clear to the user which alert triggered the system.
FR6	Intelligence	The intelligence shall be able to run on-premise and be triggered via API requests to the interface server, which never calls the model directly (Section 6).	High	The intelligence should process all the information within the company network and not use any external APIs due to privacy concerns.
FR7	Data	User feedback will be sent to a database hosted on premise within the company.	Low	This gives insight to the developers where to improve the intelligence system.
FR8	Intelligence trigger	The intelligence should receive a URL on every main-frame navigation to a new page, i.e. when any part of the URL changes and a new page loads, not only the domain. In-page jumps (#fragment changes) and internal pages (chrome://, about:, localhost) are not checked.	Med	This will make it so that the system automatically starts the intelligence to prevent any mistakes during browsing.
FR9	Override and report	The user can proceed despite a warning and report a wrong verdict (moved from the former AI-8).	High	Users stay in control, and false alarms reach the developers.
FR10	Distributed processing	The interface server sends each URL to the model workers through a message queue (RabbitMQ) and waits at most 2 s for the reply.	High	Slow or failing inference never blocks the user, and workers can be added for more load.
FR11	Health status	GET /health reports whether the API and the queue are up. The extension shows this as a green, orange or red status dot.	Med	Users and admins can see at a glance whether protection is active.
FR12	Terminal scanner	The command secsai --check <url> checks a URL through the API from the terminal.	Low	Quick demos and scripted checks without a browser.

3.4 Non-functional requirements
ID	Feature	Description	Priority	Result
NFR1	Data storage	User feedback data will be stored anonymously and users will be informed of the data being stored according to the GDPR.	High	This will follow the laws of the European Union. User data will be stored anonymously for privacy reasons.
NFR2	Accessibility	The extension shall be automatically usable by the employees on company laptops and computers.	Med	This will make it so our system can be implemented company wide in all sorts of departments.
NFR3	Load times	The intelligence shall return a result within 3 seconds.	High	The user shouldn't have to be delayed in their internet use by our system.
NFR4	Warning visual	The warning shall be able to be removed with 1 click. It shall clearly state that it is generated by the system.	Low	This will smoothen our users' experience and allow them to recognize the warning.
NFR5	Start-up	The system shall be able to start on start-up of the browser within 1 minute.	Med	The user won't have to enable the extension, which keeps the system simple to use.
NFR6	Uptime	The whole system shall be able to receive feedback and API calls 24/7 during the deployment of the system.	High	This will make data collection possible at all times and our KPIs should give a clear view of the deployment of the system.
NFR7	Codebase	The code of the system shall be well-documented by the developers and viewable by the developers and course instructors.	High	This will make implementing new features easier and results in all code being readable.
NFR8	Reliability	If any backend part fails, the user still gets a clear answer within 2 s: an error code (502, 503 or 504) from the API and a "couldn't verify" notice in the extension, never a crash or a made-up verdict. A job held by a crashed worker is re-queued. After any service restarts, the system recovers without manual steps.	High	The browser keeps working when the backend does not.
NFR9	Security	All input is validated (a JSON object with a URL of at most 2,048 characters). Database queries are parameterised, and request logs store no URLs.	High	Hostile URLs cannot crash the server or reach the database as code.
NFR10	Coverage of the intelligence	The model shall return a verdict for every valid URL, including raw IP addresses, deep subdomains, long paths and query strings, with or without a scheme. Phishing, malware and defacement links are all covered and reported as malicious.	High	No type of link silently bypasses the check.

3.5 AI-specific requirements
The requirements below exist because the system uses trained machine-learning models instead of fixed rules. The model sorts each URL into one of two classes, benign or malicious, based on probability, not certainty. That means it can be wrong, it loses accuracy as malicious links change, and it cannot explain itself unless we build that in. These traits create needs that a normal rule-based program would not have.
ID	Requirement	Why it is AI-specific
AI-1	The system should sort each URL into benign or malicious and return that label.	The verdict comes from a trained model, not a fixed rule, so the output is a prediction and not a guaranteed answer.
AI-2	For every verdict the model should also return a confidence score, and if that score is too low the result should be shown as uncertain instead of a firm answer.	Only a model can give a confidence value. It is needed so the system does not sound certain when it is not.
AI-3	When a URL is flagged, the system should show the main reasons for the decision (for example suspicious keywords, an IP address used instead of a domain name, very random-looking text, or an unusually long link).	Links to the goal that the system must explain why it flagged something. A model is a black box unless we design it to show its reasons.
AI-4	The model should be set up to catch as many bad URLs as possible, even at the cost of some false alarms, and training should make up for uneven class sizes so rare threats are still caught. Target: recall ≥ 0.85 on the malicious class, while keeping benign recall high so users are not spammed with false alarms.	Missing a bad link is worse than a false alarm. This balance is set by weighting the classes and tuning the model.
AI-5	The model should hit agreed performance targets on a held-out test set before it is deployed (for example macro-F1 ≥ 0.90).	Performance has to be measured on unseen data, which is specific to ML systems.
AI-6	The model should return a verdict within the time budget (aim for under 1 second per URL) and should be light enough to run at small scale.	This limit is why a light model was chosen over a heavy deep-learning one. It is an AI-specific trade-off between speed, size, and accuracy.
AI-7	Training data should be correctly labelled, with duplicate URLs and conflicting labels removed (to avoid data leakage). URLs sent in for a verdict should not be stored or reused for anything else unless the user agrees.	Data quality, leakage, and how training data is handled are all ML-specific issues. Supports the privacy-friendly goal.
AI-8	The model must not rely on artefacts of the training data. Features that leak the label (such as the URL scheme in our dataset) are removed, and before release the model is checked on a fixed bank of well-known safe sites, none of which may be flagged.	A model can score well by learning a shortcut instead of the real signal. A rule-based program cannot.
3.6 Requirement status
Met as specified: UR1, UR2, UR3, UR4, UR6, UR7, FR1-FR12, NFR3, NFR4, NFR5, NFR7, NFR9, NFR10, AI-3 to AI-8. The other requirements are listed below.
ID	Status	Explanation
UR5	Partly met	The extension shows a neutral "couldn't verify" badge and never blocks navigation. The badge is easy to miss, so a user heading to a suspicious site while the backend is down is not clearly warned.
NFR1	Partly met	Feedback is stored anonymously, but the extension does not yet show a privacy notice.
NFR2	Not met	The extension is installed manually in developer mode. A company-wide rollout through managed browser policies is future work.
NFR6, NFR8	Partly met	Services restart independently and a crashed worker's job is re-queued, but after RabbitMQ restarts the services do not reconnect automatically.
AI-1	Changed	Binary instead of four classes. For the user, phishing, malware and defacement lead to the same action (go back or proceed), and the binary model no longer flags well-known domains.
AI-2	Partly met	Every verdict has a confidence score, but there is no separate "uncertain" label yet.
AI-5	Not met	The model does not meet the required macro-F1 score of ≥ 0.90, achieving a macro-F1 score of 0.8636.

4. Project Management and Implementation
Erik was the Scrum Master most weeks. His tasks included scheduling and making sure the Trello board was up to date with what we were doing.
The experience with using tasks felt very smooth. We started with dividing the work and then making corresponding user stories. These tasks were not fully equipped with user and system requirements. We are now slowly building upon these tasks when we create new ones by providing them with definitions of done and stricter deadlines.
Our experience using Git and GitHub went better than expected. Most of the team members hadn't heard of using uv to manage Python environments, so Erik wrote a quick installation and user guide for the rest of the team. The only problem we encountered was that Filip didn't know he shouldn't edit the uv.lock file directly. Thanks to the version control we had in place, this was easily fixed during the next practical.
GitHub repository (public, so the code, tests and commit history can be checked directly): https://github.com/ktilburgtilburg/SECSAI-group-6
We have 2 branches: a main branch and a dev branch for prototyping.
5. Implementation and Testing
5.1 Unit tests
We use unit tests to check small parts of our program separately. Each test gives a function a particular input and checks whether it produces the expected result.
For example, we test the functions that check and clean URLs. We check that spaces around a URL are removed, that empty inputs are rejected, and that URLs stay within the allowed length. We also test that private information, such as passwords or information in a query, is removed before a URL is stored. Other unit tests check the features used by the prediction model. These include recognising IP addresses, identifying words often found in suspicious URLs, and detecting encoded characters.
These tests call the functions directly. They do not need a running server, a browser, or a database. We also distinguish tests of the temporary prediction model from tests of production functions: checking the temporary model's behaviour does not prove that the trained model detects threats accurately.
ID	Test case	Test data (input)	Expected output	Result
U1	Trim spaces around a URL	"  https://example.com  "	"https://example.com"	Pass
U2	Reject empty input	"" and "   "	Input error: URL must be non-empty	Pass
U3	Enforce the length limit	A URL of 2,049 characters	Input error: at most 2,048 characters	Pass
U4	Remove private data before storing	https://user:pw@Example.com:8080/reset?token=abc	"https://example.com"	Pass
U5	Detect a raw IP address	http://192.168.0.1/login vs. https://example.com	IP flag 1 vs. 0	Pass
U6	Detect suspicious words	secure-login-verify.com vs. example.com	Word flag set vs. not set	Pass

5.2 Component and integration tests
Our component and integration tests check larger parts of the application and how they work together. For the backend, we send requests through Flask's test client and inspect the responses. We check that valid requests receive the expected response format and that invalid requests receive a suitable error. For example, a request without a URL should return an input error. If prediction fails, the backend should return a clear error response instead of exposing internal details.
We also test the connection between the feedback endpoint and the database. These tests use a real temporary database, keeping test reports separate from normal application data. We submit feedback and then read the database to confirm that it was saved correctly. We check that private URL information is removed, repeated reports are handled correctly, and saved reports remain available through another database connection.
Failure handling is another part of the tests. We deliberately cause a storage problem, check the error response, and then confirm that saving works again once storage is available. We also test command-line results and extension behaviour when the backend is unavailable. The extension test uses simulated browser events, so it supports our checks but does not replace testing in an actual browser. Overall, all 87 Python tests passed locally at the time of Task 5.
ID	Test case	Test data (input)	Expected output	Result
I1	Valid assessment request	POST /api/v1/assess with {"url": "https://example.com"}	200 with is_malicious, category, confidence and explanations	Pass
I2	Missing URL	POST /api/v1/assess with {} and with no body	400 with a JSON error message	Pass
I3	Prediction fails	Model replaced by a function that raises an error	JSON error without internal details (500 at the time; 502/503/504 since Task 6)	Pass
I4	Feedback saved, private data removed	Report for https://user:pw@Example.com/reset?token=abc, sent twice; then read the temporary DB	First "saved", then "duplicate"; one row containing only https://example.com	Pass
I5	Storage failure and recovery	Database made unavailable, then restored	500 "Could not save feedback", then the next report is saved	Pass
I6	CLI exit codes	secsai --check on a safe URL, a flagged URL and a blank URL	Exit codes 0, 1 and 2	Pass
I7	Extension with backend down	Simulated navigation events while the API is unreachable	Navigation is not blocked and the extension does not crash	Pass

Why these tests. The unit tests cover the code that guards the edges of the system: input validation, privacy and the model's features. A bug there means a crash, a privacy leak or wrong input for the model. The integration tests follow the paths a real user triggers, including the failure paths, because the system has to fail safely rather than block the browser.
Later change: since Task 6 the API no longer calls the model directly, so the temporary predictor was removed. The final suite has 106 Python tests plus the extension tests (Section 7.1).
5.3 Implementation progress
We developed the project in stages, starting with understanding the data. During September, we explored different scam-related datasets and examined their contents, missing information, duplicates, and categories. We then added model experiments, including data cleaning, feature extraction, training, and evaluation. This provided a foundation for choosing how the application would assess URLs.
In October, we moved towards a usable application. We first added the backend and its basic endpoints, using a temporary predictor so that the application could be developed before the trained model was connected. We then added production feature extraction, model training, and prediction, and connected prediction to the backend.
The application grew further with browser navigation checks, feedback storage, and a command-line tool. We added shared input validation and removed private information from stored URLs. Tests were introduced alongside these features to check normal behaviour and errors.
The latest work added a browser popup, a warning screen, feedback actions, and further tests for individual functions and recovery after failures. Development was concentrated in several active periods, with a gap in October, but each stage built on the previous work and expanded what the application could do.
6. Task 6 - Distributed Architecture
We split the URL threat checker into three logical servers that run as containers on one machine with Docker Compose. The interface never calls the model, so slow or failing inference cannot block users.
 
Figure 1. Distributed architecture of the system.
1. Interface server. A Flask REST API is the only entry point for the extension and the CLI. It validates input, stores feedback in SQLite, logs each request without URLs and reports API and queue health on GET /health. It sends each URL to RabbitMQ and waits at most 2 s, returning 502, 503 or 504 on failure. Keeping the model out of the API keeps it light, the timeout stops slow inference from hanging the browser, and on any error the extension shows "couldn't verify" without blocking navigation.
2. AI component servers. Each worker container loads the binary benign/malicious classifier once at startup, re-validates the URL, runs predict() and returns the result with its worker_id. Loading the model only once removes per-request start-up cost, and because the workers are stateless they scale with --scale worker=3. We moved to a binary model because the user's action is the same for phishing, malware and defacement: go back or proceed. Together with the feature fixes in Section 7.1, the new model no longer flags well-known domains such as google.com.
3. Orchestrator (RabbitMQ). The API publishes each job to assess_requests with a reply_to queue and a correlation_id; the worker replies to that queue. Using a queue decouples the servers, so each can restart or scale on its own. prefetch_count=1 gives fair dispatch, and acknowledging only after replying means a crashed worker's job is re-queued. We chose RabbitMQ because it provides this request/reply routing out of the box.
Verification. With 3 workers, 6 test requests were split evenly across the 3 worker_ids, the RabbitMQ dashboard showed 3 consumers, and unit, API and extension tests pass.
Limits. This setup is built for a single-machine demo. For many users, the interface server, the broker and the workers would run on separate hosts, with more than one RabbitMQ node so the broker is not a single point of failure.

 7. Task 7 - Wrapping Up
7.1 Final state of the system
Code. We removed dead code, including the old direct predict() call in the API and the old multi-class code, ran ruff format and ruff check across all services, added docstrings to the main functions, and rewrote the README so anyone can start the whole system with docker compose up. All work is merged into the master branch.
Tests. The final suite has 106 Python unit and contract tests, Node tests for the extension's failure handling, and a script (verify_system.py) that checks load, a worker crash, a broker outage and recovery. All of them pass on master.
Operation. Starting from a fresh clone and following only the README, the full flow works: extension → interface server → RabbitMQ → worker → verdict. With --scale worker=3, the RabbitMQ dashboard shows three consumers, and stopping a worker re-queues its job. The check found two problems we have not fixed yet: after RabbitMQ restarts, the services do not reconnect automatically, and when the backend is down the "couldn't verify" badge is easy to miss. Both are listed in Section 3.6.
AI. The workers load the final binary Random Forest (models/classifier.joblib) once at startup, and a warm prediction takes 14.6 ms per URL. The final model achieves a macro F1-score of 0.8636 on the held-out test set using a classification threshold of 0.55. At this threshold, the model achieves a malicious-class precision of 82.68% and recall of 80.48%, with a false positive rate (FPR) of 8.24%. Its output matches the API contract: is_malicious, category (benign or malicious), confidence and explanations.
Getting there took two fixes. First, our early models scored 94-97% accuracy, but partly for the wrong reason: 91.7% of benign URLs in the dataset had no scheme (google.com), while malicious ones mostly had one, so the model learned "scheme = malicious". We now strip the scheme before extracting features. We chose not to add schemes to scheme-less URLs, because that would invent data we don't have. The trade-off is that the model can no longer distinguish http://google.com from https://google.com, but real phishing can use both, so scheme is not a reliable signal. Second, our first deployed model flagged almost every site, including google.com. The dataset had almost no short benign domains (1 in 422,469), and the features had no sense of brands. As a stop-gap we added a google.com bypass. The real fix was a brand-distance feature: the edit distance from a URL's domain to the nearest well-known brand, so google.com scores 0 and go0gle.com scores 1. It became the model's strongest feature (14.7% importance).
7.2 Value Sensitive Design
With Value Sensitive Design (VSD), we would have started from the values at stake instead of adding them along the way. Four values matter here: privacy (a URL reveals what someone reads), user autonomy, trust and transparency, and fairness.
Design. We got autonomy and transparency right: users can choose "Proceed Anyway", and the warning explains why a site was flagged. With VSD, we would have asked real users early what they expect from a warning and what data they would share, and decided up front who reviews false-alarm reports.
Development. Logs store no URLs, feedback keeps only the hostname, and the extension shows "couldn't verify" instead of blocking. But privacy came late: we only stripped URLs after noticing they can contain tokens and emails. With VSD, it would have been a requirement from day one.
Testing. We would test on non-English and small-business sites, which a model trained mostly on large sites may flag unfairly, and track false alarms per group. Our first deployed model flagged even google.com, which shows how quickly this goes wrong.
7.3 Environmental impact
AI component. Our Random Forest is a small classical model, not deep learning, so its direct footprint is minimal. Training takes about 3 minutes, or about 10 minutes for the full pipeline, on a laptop CPU. At an assumed 50 W, the full pipeline uses roughly 0.008 kWh, about 1.5 g CO₂e at the EU average of 178 g CO₂e/kWh (EEA, 2025 estimate). A warm prediction takes 14.6 ms, which comes to about 0.04 g CO₂e per 1,000 checks.
Non-AI part. Most of the energy goes elsewhere: the RabbitMQ and worker containers run all day even when idle, Docker images are rebuilt during development, and the extension calls the server on every page visit. To cut this, we could cache URLs that were already checked, skip well-known safe domains, scale down to one worker when traffic is low, and keep images and model files small.
7.4 Teamwork
•	Erik - backend (API, feedback storage, CLI, interface server) and scrum master for most of the project: created and managed the Trello tasks and kept work on schedule.
•	Filip - frontend (browser extension, warning screen, popup) and design; put together most of the reports, ran the final system check and updated the requirements.
•	Alexander - modeller: built the main model and made sure its accuracy was not misleading.
•	Jarod - modeller: feature extraction, the AI worker server and the environmental analysis.
•	Koen - tester: the test bank, automated tests, and load and failure tests.

We started together: everyone explored a different dataset before we picked a project. After that, we met every week in person at university, and as far as we remember everyone attended every meeting. There we agreed on the next week's tasks, which became Trello cards with clear goals, and made the big decisions together. Day to day, we talked in a WhatsApp group. To work in parallel, we agreed on interfaces first: frontend and backend met to design the API, and the modellers agreed on the predict() format. We designed the tests together, reviewed each other's code quickly, and tested the extension together in person to check that everyone's parts worked when combined.
Three challenges stood out. Our first idea (a multimodal scam detector with a strong model and an explainable-AI component) was too much for the time we had, so we narrowed it to URLs. Our model then blocked almost every website despite high test accuracy, which Alexander traced to shortcuts in the data and fixed (Section 7.1). Finally, feedback could leak private data, since URLs can contain tokens and emails, so we store only the hostname.
Sources
European Environment Agency (EEA). Greenhouse gas emission intensity of electricity generation in Europe. https://www.eea.europa.eu/en/analysis/indicators/greenhouse-gas-emission-intensity-of-1
