# Prajna Daily — 2026-11-27

_What's trending in tech worldwide today (Hacker News, GitHub, new AI papers, Wikipedia), grouped by category and answered automatically with citations. Mode: **NVIDIA NIM (8/8 answers by the LLM)**. Updated daily by GitHub Actions — [archive](digest/data/)._

## Chips & Hardware

### Hard Drive pricing has gotten bad — what is this about and why does it matter?

<sub>▲ 532 points on Hacker News · 451 comments</sub>

Hard drive pricing has become fragmented and difficult to track across retailers, as highlighted by the ListofDisks project [1]. This tool monitors prices across Amazon, B&H, Best Buy, Newegg, Office Depot, ServerPartDeals, and Walmart, normalizing listings into canonical products to allow side-by-side comparisons [1]. It tracks 90-day median $/TB and historical-low pricing to help users identify genuine deals amid marketplace noise [1].

Manufacturer reliability varies significantly [4]. Based on Backblaze dataset analysis, HGST drives show the lowest failure rates—about 41% of Seagate's [4]. Toshiba's rates are slightly above Seagate's, while Western Digital (WD) rates are significantly above HGST's but still only about 52% of Seagate's when controlling for age, capacity, form-factor, and temperature [4].

Price tracking matters because HDDs remain dominant secondary storage despite solid-state alternatives [3][6]. While HDDs offer high capacity at lower cost per terabyte, reliability and pricing transparency vary by manufacturer and retailer. Tiering and caching strategies in storage systems [6] automatically move data between media types based on access patterns, balancing performance needs with cost considerations.

Historically, IBM introduced the first HDD in 1956 [3][7], and the technology has evolved from data-center-only devices to ubiquitous consumer storage. Modern HDDs store data on rigid platters with magnetic heads, maintaining random-access capabilities while offering non-volatile retention [3].

<sub>Sources: [1] [Show HN: ListofDisks – hard drive price index across 7 retailers not just Amazon](https://news.ycombinator.com/item?id=46992426) · [2] [Modern Hard Disk Media Issues](https://doi.org/10.1007/978-94-010-0624-8_3) · [3] [Hard disk drive](https://en.wikipedia.org/wiki/Hard_disk_drive) · [4] [Are There Manufacturer Differences in Hard-Drive Reliability?](https://doi.org/10.1109/tcc.2026.3679404) · [5] [Ask HN: Is there a good cloud provider to archive large files to?](https://news.ycombinator.com/item?id=36333417) · [6] [A Survey on Tiering and Caching in High-Performance Storage Systems](https://arxiv.org/abs/1904.11560v1) · [7] [History of hard disk drives](https://en.wikipedia.org/wiki/History_of_hard_disk_drives) · [8] [Examining the feasibility of the urban mining of hard disk drives](https://doi.org/10.1016/j.jclepro.2019.119216)</sub>

## AI & ML

### AI made self-hosting fun again — what is this about and why does it matter?

<sub>▲ 1,028 points on Hacker News · 488 comments</sub>

Self-hosting AI has re-emerged as a strategic choice for organizations prioritizing data sovereignty and cost control. Platforms like Alien [1][2] enable deploying software directly into customers' AWS, GCP, or Azure accounts, ensuring no sensitive data leaves the customer's environment while maintaining a fully managed vendor experience. This approach addresses enterprise concerns about operating third-party software and losing visibility into deployments [1][2]. Open-source frameworks such as OpenClaw [7] and n8n [6] further support self-hosted AI by providing adaptive educational AI and workflow automation for cybersecurity, respectively. These tools offer significant advantages in cost, customization, and data control, though they present challenges in technical deployment complexity and psychometric maturity [7]. Meanwhile, Pythia [5] provides a framework for analyzing web hosting environments, revealing that under 11% of popular domains are self-hosted, highlighting the historical dominance of third-party hosting [5].

<sub>Sources: [1] [Show HN: Alien – Ship to your customer's cloud](https://github.com/alienplatform/alien) · [2] [Show HN: Deploy to your customers' AWS/GCP/Azure accounts](https://news.ycombinator.com/item?id=47818157) · [3] [Show HN: Plandex v2 – OSS AI coding agent w/ diff sandbox, full auto, 2M context](https://plandex.ai) · [4] [Show HN: Whilio – AI chatbot that learns your site and explains user behavior](https://whilio.com/) · [5] [Pythia: a Framework for the Automated Analysis of Web Hosting Environments](https://arxiv.org/abs/1903.06925v2) · [6] [Self-Hosted Workflow Automation for AI-Based Cybersecurity Operation](https://doi.org/10.53735/cisse.v13i1.241) · [7] [Exploring OpenClaw’s potential for adaptive, self-hosted educational AI](https://doi.org/10.3389/feduc.2026.1859178) · [8] [AI Chips: What They Are and Why They Matter](https://doi.org/10.51593/20190014)</sub>

### Group chat where your AI talks behind your back — what is this about and why does it matter?

<sub>▲ 621 points on Hacker News · 262 comments</sub>

AI gossip refers to generative AI chatbots producing rich streams of text that appear truth-apt without concern for truthfulness, potentially fabricating social information like rumors or private details [1][2]. This differs from simple hallucination by focusing on the social dynamics of misinformation. The phenomenon matters because it can create "technosocial harms"—distinct harms that follow from AI-mediated social interactions, such as reputational damage or relational disruption [2].

Key aspects of AI gossip include:

- **Mechanism**: Chatbots produce text that looks truth-apt without any concern for truthfulness, making them capable of generating gossip-like content about historical events, figures, legal cases, and biographies [1][2]
- **Social impact**: The "technosocial harms" framework identifies specific harms that emerge from AI-mediated social interactions, particularly around privacy and relational dynamics [2][4]
- **Privacy concerns**: AI companions lower disclosure thresholds, encouraging intimate self-disclosure while users recognize corporate control over their data, creating unique privacy management challenges [4]
- **User behavior**: People may disclose more to AI companions than intended, treating shared information as relationally held despite knowing corporate control exists [4]

The concern about "group chat where your AI talks behind your back" relates to how AI systems might share or gossip about user information across contexts, potentially violating privacy expectations and creating social harm through rumor-spreading or information leakage [4][5].

<sub>Sources: [1] [AI Gossip](https://doi.org/10.48550/arxiv.2508.08143) · [2] [AI gossip](https://doi.org/10.1007/s10676-025-09871-0) · [3] [Show HN: Knowledgework – AI Extensions of Your Coworkers](https://knowledgework.ai/) · [4] [Chatting with confidants or corporations? Privacy management with AI companions](https://doi.org/10.1093/jcmc/zmag014) · [5] [Show HN: AgentSea – Private, fast, and safe AI chat to access latest AI models](https://agentsea.com) · [6] [Google's Gemini AI and Privacy Concerns: What You Need to Know](https://www.geeksmatrix.com/2024/07/googles-gemini-ai-and-privacy-concerns.html) · [7] [Security And Privacy Concerns In Generative AI](https://doi.org/10.2139/ssrn.5052837) · [8] [ChatGPT](https://en.wikipedia.org/wiki/ChatGPT)</sub>

### What does the new AI research paper "Stable Gated DeltaNet-2: Understanding and Mitigating Recurrent State Instability" propose, and why does it matter?

<sub>▲ 126 upvotes on Hugging Face Daily Papers</sub>

Stable Gated DeltaNet-2 (SGDN-2) proposes symmetric erasure to ensure non-expansive state propagation and decay-regulated residual writing to preserve writing flexibility [1]. This resolves training failures in long-context training caused by asymmetric reading and modification directions during erasure, which previously led to exponential state growth even without new writes [1]. Theoretically, the method establishes an $O(\sqrt{T})$ upper bound on recurrent state growth while retaining chunkwise parallel computation [1]. Experiments on ~1.6B parameter models show SGDN-2 achieves stable training alongside improved long-context retrieval, boosting the 128K average RULER score by 6.80 points in the recurrent setting and average accuracy across nine downstream tasks by 0.62 points in the hybrid setting compared to GDN-2 [1].

<sub>Sources: [1] [Stable Gated DeltaNet-2: Understanding and Mitigating Recurrent State Instability](https://arxiv.org/abs/2611.34051v1) · [2] [Gated Delta Networks: Improving Mamba2 with Delta Rule](https://doi.org/10.48550/arxiv.2412.06464) · [3] [SANE: State Anomaly Neutralization for Stable Extreme-Context Delta-Rule Models](https://doi.org/10.48550/arxiv.2608.22354) · [4] [Kaczmarz Linear Attention](https://arxiv.org/abs/2605.08587v1) · [5] [Gated KalmaNet: A Fading Memory Layer Through Test-Time Ridge Regression](https://doi.org/10.48550/arxiv.2511.21016) · [6] [Gated KalmaNet: A Fading Memory Layer Through Test-Time Ridge Regression](https://arxiv.org/abs/2511.21016v3) · [7] [MemT-1.0: Towards Memory-Native Evolution](https://doi.org/10.48550/arxiv.2610.26825) · [8] [Taylor-Calibrate: Principled Initialization for Hybrid Linear Attention Distillation](https://doi.org/10.48550/arxiv.2606.16429)</sub>

### What does the new AI research paper "OS-Omni: Benchmarking Generalist Computer-Using Agents on Long-Horizon Workflows Across Platforms" propose, and why does it matter?

<sub>▲ 101 upvotes on Hugging Face Daily Papers</sub>

OS-Omni proposes a live cross-platform benchmark and execution environment for evaluating computer-using agents across Windows, Ubuntu, macOS, iOS, Android, and Web environments [1][2]. It matters because existing benchmarks typically isolate single platforms, leaving unclear whether a single generalist agent can execute long-horizon workflows spanning multiple operating systems and persistent application states [1][2]. The benchmark releases tasks in versioned waves of 300 each; v1 contains 48 tasks per platform and 12 cross-platform workflows pairing a desktop with an Android phone [1][2]. OS-Omni provides reproducible initialization, platform-specific adapters, trajectory logging, executable final-state evaluators, and controlled service-backed applications for workflows involving account, cart, budget, calendar, and message states [1][2]. Human studies show OS-Omni tasks require 67.54 interaction steps, substantially exceeding OSWorld references of 15.0 steps [1][2]. On v1, the strongest evaluated agent, Claude Opus 5.5, reaches 68.5% average success, trailing the 77.3% human reference by 8.8 points; the gap is uneven across platforms, with frontier models exceeding humans on Linux but trailing them by more than 25 points on iOS and macOS [1][2]. These results indicate that current agents remain far from platform-robust, long-horizon computer use, especially when success requires sustained state tracking and durable final-state changes [1][2].

<sub>Sources: [1] [OS-Omni: Benchmarking Generalist Computer-Using Agents on Long-Horizon Workflows Across Platforms](https://doi.org/10.48550/arxiv.2611.34232) · [2] [OS-Omni: Benchmarking Generalist Computer-Using Agents on Long-Horizon Workflows Across Platforms](https://arxiv.org/abs/2611.34232v1) · [3] [OfficeBench: Benchmarking Language Agents across Multiple Applications for Office Automation](https://doi.org/10.48550/arxiv.2407.19056) · [4] [TOBench: A Task-Oriented Omni-Modal Benchmark for Real-World Tool-Using Agents](https://doi.org/10.48550/arxiv.2605.16909) · [5] [OmniGUI: Benchmarking GUI Agents in Omni-Modal Smartphone Environments](https://doi.org/10.48550/arxiv.2605.18758) · [6] [Focused Omni-Modal GUI Agents](https://doi.org/10.48550/arxiv.2610.26203) · [7] [Deep Research of Deep Research: From Transformer to Agent, From AI to AI for Science](https://doi.org/10.48550/arxiv.2603.28361) · [8] [VIT-LENS: Towards Omni-modal Representations](https://doi.org/10.1109/cvpr52733.2024.02516)</sub>

## Gadgets

### What is the new open-source project VIctory (An attempt at running GTA VI on PC), and why is it getting attention?

<sub>★ 13,750 GitHub stars since 2026-11-23 · Rust</sub>

Victory is an open-source project aimed at running Grand Theft Auto VI on PC, gaining attention as one of the first attempts to reverse-engineer and port the 2026 title to the platform. Because GTA VI is a recent commercial release, modding it presents significant technical challenges. The project leverages the precedent set by GTA V modding, which relies on third-party software due to the lack of official editing tools from Rockstar Games [2]. Notably, the open-source development environment for self-driving vehicles was built on top of GTA V [4], demonstrating the game's utility beyond entertainment. GTA VI's development began after the 2018 launch of Red Dead Redemption 2, which itself had a development cycle lasting over eight years [8]. The open-source community's interest in Victory reflects broader trends in GTA modding, where users alter gameplay logic and asset files to modify their experience [2].

<sub>Sources: [1] [Grand Theft Auto VI](https://en.wikipedia.org/wiki/Grand_Theft_Auto_VI) · [2] [Grand Theft Auto modding](https://en.wikipedia.org/wiki/Grand_Theft_Auto_modding) · [3] [Grand Theft Auto V](https://en.wikipedia.org/wiki/Grand_Theft_Auto_V) · [4] [An open-source development environment for Self- driving vehicles](http://hdl.handle.net/10609/63765) · [5] [Grand Theft Auto (video game)](https://en.wikipedia.org/wiki/Grand_Theft_Auto_(video_game)) · [6] [Grand Theft Auto: The Trilogy – The Definitive Edition](https://en.wikipedia.org/wiki/Grand_Theft_Auto:_The_Trilogy_%E2%80%93_The_Definitive_Edition) · [7] [List of video games in development](https://en.wikipedia.org/wiki/List_of_video_games_in_development) · [8] [Red Dead Redemption 2](https://en.wikipedia.org/wiki/Red_Dead_Redemption_2)</sub>

### Who or what is Grand Theft Auto VI, and what are the key facts to know?

<sub>👁 151,092 Wikipedia views yesterday</sub>

Grand Theft Auto VI is a 2026 action-adventure game developed and published by Rockstar Games [1]. It is the eighth main entry in the series, following 2013's Grand Theft Auto V [1][6], and features a fictional US state of Leonida based on Florida [1]. The story follows criminal duo Jason Duval and Lucia Caminos as they lead a life of crime to escape corrupt police [1]. The game's open world includes Miami-inspired Vice City and various side activities [1]. Development began preliminary work in 2014 after GTA V, with principal production starting after the 2018 launch of Red Dead Redemption 2; Rockstar's global development teams had more than doubled since then [1]. A promotional trailer, "An Extended Look," premiered on Netflix in August 2026 and topped English language trailer charts in 87 countries [4]. The original score is composed by the French electronic duo Justice, scheduled for release on 11 December 2026 [3]. A soundtrack album, "The Album," was released on November 20, 2026, through Atlantic Records and Take-Two Interactive, featuring artists such as Cardi B, Dua Lipa, Lana Del Rey, Morgan Wallen and Travis Scott [2].

<sub>Sources: [1] [Grand Theft Auto VI](https://en.wikipedia.org/wiki/Grand_Theft_Auto_VI) · [2] [Grand Theft Auto VI: The Album](https://en.wikipedia.org/wiki/Grand_Theft_Auto_VI:_The_Album) · [3] [Grand Theft Auto VI: Original Score](https://en.wikipedia.org/wiki/Grand_Theft_Auto_VI:_Original_Score) · [4] [Grand Theft Auto VI: An Extended Look](https://en.wikipedia.org/wiki/Grand_Theft_Auto_VI:_An_Extended_Look) · [5] [Grand Theft Auto](https://en.wikipedia.org/wiki/Grand_Theft_Auto) · [6] [Grand Theft Auto V](https://en.wikipedia.org/wiki/Grand_Theft_Auto_V) · [7] [Niko Bellic](https://en.wikipedia.org/wiki/Niko_Bellic) · [8] [Grand Theft Auto: Vice City](https://en.wikipedia.org/wiki/Grand_Theft_Auto:_Vice_City)</sub>

## Software & Dev Tools

### What is the new open-source project xcl (Xbox Series compatibility layer for Windows - runs console game code natively, reimplements the console system libraries and recompiles RDNA2 shaders to DXIL), and why is it getting attention?

<sub>★ 8,711 GitHub stars since 2026-11-20 · Rust</sub>

xcl (Xbox Series compatibility layer for Windows) is an open-source project that runs Xbox Series X/S console game code natively on Windows by reimplementing console system libraries and recompiling RDNA2 shaders to DXIL. It is gaining attention because it allows playing Xbox Series games on PC without emulation overhead, leveraging the Windows ecosystem while supporting the console's hardware architecture [3][4].

<sub>Sources: [1] [Windows 11](https://en.wikipedia.org/wiki/Windows_11) · [2] [Xbox (app)](https://en.wikipedia.org/wiki/Xbox_(app)) · [3] [Your visualisations are going places: SciVis on gaming consoles](https://doi.org/10.1007/s12650-024-01035-4) · [4] [Xbox (console)](https://en.wikipedia.org/wiki/Xbox_(console)) · [5] [Xbox (division)](https://en.wikipedia.org/wiki/Xbox_(division)) · [6] [Microsoft Windows](https://en.wikipedia.org/wiki/Microsoft_Windows) · [7] [Playing Spy Games: a Surveillant Platform Study of Microsoft's Xbox 360](http://hdl.handle.net/1807/80299) · [8] [TDOA-based acoustic source localization in the space–range reference frame](https://doi.org/10.1007/s11045-013-0233-8)</sub>

