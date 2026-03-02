[Image: CHRIST Logo]

A Project Report on

COMPLIANCE AUTOMATION SYSTEM - PRIVACY
POLICY ANALYSIS USING RAG AND AGENTIC AI

Submitted in partial fulfillment of the requirements for the degree of
BACHELOR OF TECHNOLOGY

in

Computer Science and Engineering - Artificial

Intelligence and Machine Learning

by

Name

Register Number

S Shashank Reddy

2262143

Siddharth Ramachandran

2262158

Under the Guidance of

Ashly C Dhanu

and

Neethu PS

AI and Data Science Engineering

School of Engineering and Technology, CHRIST (Deemed to be University), Kumbalgodu, Bengaluru -560 074

March-2026

Vision

"Excellence and Service"

Mission

"CHRIST (Deemed to be University) is a nurturing ground for an individual's holistic development to make effective contribution to the society in a dynamic environment."

Core Values

Faith in God

Moral Uprightness

Love of Fellow Beings

Social Responsibility

Pursuit of Excellence

Department Vision

"To excel in Human-Centred AI and Data-Driven Innovation "

Department Mission

M1: Empowering individuals to ethically harness data and AI through accessible and value-driven curriculum.

M2: Foster a dynamic research environment that advances innovative and impactful solutions for the betterment of global well-being.

M3: Innovate scientific knowledge and entrepreneurship through academia and Industry collaborations.

Program Educational Objectives (PEOs)

PEO1: Professional Acumen: Understand, analyze and design solutions with professional competency for the real world problems.

PEO2: Critical Analysis: Develop software/embedded solutions for the requirements, based on critical analysis and research.

PEO3: Team work: Function effectively in a team and as an individual in a multidisciplinary/multicultural environment.

PEO4: Life Long Learning: Accomplish holistic development comprehend- ing professional responsibilities

Program Outcomes (POs)

PO1: Engineering Knowledge: Apply knowledge of mathematics, natural science, computing, en- gineering fundamentals and an engineering specialization to develop the solution of complex engineering problems.

PO2: Problem Analysis: Identify, formulate, review research literature and analyze complex engi- neering problems reaching substantiated conclusions with consideration for sustainable development.

PO3: Design/Development of Solutions: Design creative solutions for complex engineering prob- lems and design/develop systems/components/processes to meet identified needs with consideration for the public health and safety, whole-life cost, net zero carbon, culture, society and environment as required.

PO4: Conduct Investigations of Complex Problems: Conduct investigations of complex engi- neering problems using research-based knowledge including design of experiments, modelling, analysis & interpretation of data to provide valid conclusions.

PO5: Engineering Tool Usage: Create, select and apply appropriate techniques, resources and modern engineering & IT tools, including prediction and modelling recognizing their limitations to solve complex engineering problems.

PO6: The Engineer and The World: Analyze and evaluate societal and environmental aspects while solving complex engineering problems for its impact on sustainability with reference to economy, health, safety, legal framework, culture and environment.

PO7: Ethics: Apply ethical principles and commit to professional ethics, human values, diversity and inclusion; adhere to national & international laws.

PO8: Individual and Collaborative Team work: Function effectively as an individual, and as a member or leader in diverse/multi-disciplinary teams.

PO9: Communication: Communicate effectively and inclusively within the engineering community and society at large, such as being able to comprehend and write effective reports and design docu- mentation, make effective presentations considering cultural, language, and learning differences.

PO10: Project Management and Finance: Apply knowledge and understanding of engineering management principles and economic decision-making and apply these to one's own work, as a member and leader in a team, and to manage projects and in multidisciplinary environments.

PO11: Life-Long Learning: Recognize the need for, and have the preparation and ability for i) independent and life-long learning ii) adaptability to new and emerging technologies and iii) critical thinking in the broadest context of technological change.

Program Specific Outcomes (PSOs)

Artificial Intelligence: To utilize artificial intelligence principles to solve real world problems

Machine Learning: To select suitable machine learning algorithms for the given problem

Service Learning: Analyze Social Relevant Problems and design solutions through Service Learning

[Image: CHRIST Logo]

CERTIFICATE

This is to certify that S Shashank Reddy (2262143) and Siddharth Ra- machandran (2262158) has successfully completed the project work entitled "Compliance Automation System Privacy Policy Analysis using RAG and Agentic AI" in partial fulfillment for the award of Bachelor of Technology in Com- puter Science and Engineering Artificial Intelligence and Machine Learning during the year 2025-2026.

Ashly C Dhanu Assistant Professor

Neethu PS Assistant Professor

Dr Michael Moses T Head of the Department

Dr E A Mary Anita Associate Dean

[Image: CHRIST Logo]

BONAFIDE CERTIFICATE

It is to certify that this project titled "Compliance Automation System Privacy Policy Analysis using RAG and Agentic AI" is the bonafide work of

Name

Reg. No.

Department

S Shashank Reddy

2262143

AI and Data Science Engineering

Siddharth Ramachandran

2262158

AI and Data Science Engineering

Examiners [Name and Signature] 1. 2.

Name of the Candidate : Register Number: Date of Examination :

Acknowledgement

We would like to thank Dr Rev Fr Joseph CC, Vice Chancellor, CHRIST (Deemed to be University), Dr Rev Fr Viju P D. Pro Vice Chancellor, Dr Fr Jiby Jose, Director, School of Engineering and Technology, Fr Shijin P J. Assistant Director, School of Engineering and Technology, CHRIST (Deemed to be University), Dr Raghunandan Kumar R, Dean, and Dr E A Mary Anita , Associate Dean, for their kind patronage.

We would also like to express sincere gratitude and appreciation to Dr Michael Moses T, Head of the Department, AI and Data Science Engineering for giving me this opportunity to take up this project.

We also extremely grateful to our guide, Ashly C Dhanu, who has supported and helped to carry out the project. Her constant monitoring and encouragement helped us keep up to the project schedule.

We also extremely grateful to our co-guide, Neethu PS, who has supported and helped to carry out the project. Her constant monitoring and encouragement helped us keep up to the project schedule.

If outside the college-mention the organisation and the concerned people, like head of the organisation, guide and any other person you want to thank. All faculty and non-teaching staff. You may acknowledge your parents or any who supported you.

Declaration

We, hereby declare that the project titled "Compliance Automation System - Privacy Policy Analysis using RAG and Agentic AI" is a record of original project work undertaken for the award of the degree of Bachelor of Technol- ogy in AI and Data Science Engineering. We have completed this study under the supervision of Ashly C Dhanu, Department of AI and Data Science Engineering and Neethu PS, Department of AI and Data Science Engineering.

We also declare that this project report has not been submitted for the award of any degree, diploma, associate ship, fellowship or other title anywhere else. It has not been sent for any publication or presentation purpose.

We have executed this project with code of research conduct as prescribed by the university.

Place: School of Engineering and Technology, CHRIST (Deemed to be University), Bengaluru

Date: 01-03-2026

Name

Register Number

Signature

S Shashank Reddy

2262143



Siddharth Ramachandran

2262158



Abstract

Privacy policies are legal documents that describe how organizations collect, use, and protect user data. However, many organizations struggle to create compre- hensive, compliant privacy policies that meet regulatory standards such as GDPR, CCPA, and industry best practices. This project presents an AI-powered Com- pliance Automation System that automatically analyzes privacy policy doc- uments, identifies compliance gaps against the OPP-115 standard, and generates improved, compliant content using Retrieval-Augmented Generation (RAG) combined with Large Language Models (LLMs).

The system implements a three-phase pipeline: (1) Document Parsing and Text Extraction, (2) Rule-Based Compliance Checking against 10 privacy practice categories, and (3) Agentic Al-powered content generation using a multi-agent architecture. The RAG component leverages a knowledge base of 801 real privacy policy sections to ground the generation in real-world examples.

Keywords: Privacy Policy, Compliance Automation, RAG, Large Language Mod- els, NLP, Agentic AI, OPP-115

Contents

Section

Page

CERTIFICATE

V

BONAFIDE CERTIFICATE

vi

ACKNOWLEDGEMENT

vii

DECLARATION

viii

ABSTRACT

ix

LIST OF FIGURES

xiii

LIST OF TABLES

xiv

GLOSSARY

XV

1 INTRODUCTION

1

1.1 Background

1

1.2 Motivation

3

1.3 Scope

4

1.4 Problem Statement

5

1.4.1 Problem Definition

5

1.4.2 Challenges

6

2 LITERATURE SURVEY AND OBJECTIVES

8

2.1 Literature Review

8

2.1.1 Privacy Policy Analysis

8

2.1.2 OPP-115 Dataset

9

2.1.3 Retrieval-Augmented Generation (RAG)

11

2.1.4 Agentic AI and Multi-Agent Systems

13

2.1.5 Large Language Models for Legal Text

15

2.2 Objectives

16

2.2.1 Primary Objectives

16

2.2.2 Secondary Objectives

16

2.2.3 Extended Objectives (Recently Completed)

17

3 RESEARCH METHODOLOGY

18

3.1 System Architecture

18

3.1.1 High-Level Architecture

18

3.1.2 Three-Phase Processing Pipeline

18

3.1.3 Component Diagram

18

3.2 Methodology

19

3.2.1 Research Methodology

19

3.2.2 Data Collection and Knowledge Base Construction

21

3.2.3 Compliance Categories

22

3.2.4 Violation Severity Levels

23

4 ACTUAL WORK

24

4.1 Implementation Details

24

4.1.1 7.1 Directory Structure

24

4.1.2 7.2 Key Implementation Components

24

4.1.2.1 7.2.1 Document Parser

25

4.1.2.2 7.2.2 Compliance Checker

25

4.1.2.3 7.2.3 RAG Knowledge Base

25

4.1.2.4 7.2.4 Agent Orchestrator

25

4.1.3 7.3 API Endpoints

26

4.1.4 7.4 Frontend Architecture

26

4.1.4.1 7.4.1 Dashboard (index.html)

26

4.1.4.2 7.4.2 Upload Page (upload.html)

27

4.1.4.3 7.4.3 Processing Page (processing.html)

28

4.1.4.4 7.4.4 Report Page (report.html)

28

4.1.4.5 7.4.5 Analytics Page (analytics.html)

29

4.1.4.6 7.4.6 Comparison Page (compare.html)

29

4.1.4.7 7.4.7 Custom Rules Page (rules.html)

30

4.1.5 7.5 Shared Frontend Utilities

30

4.1.5.1 ComplianceAPI Client Class (api.js)

30

4.1.6 7.6 Data Persistence

30

4.1.7 7.7 Multi-Format Export System

31

4.1.8 7.8 Batch Processing

31

4.1.9 7.9 Processing Status & ETA Estimation

32

4.2 Algorithms and Flowcharts

32

4.2.1 8.1 Document Processing Algorithm

32

4.2.2 8.2 RAG Retrieval Flowchart

33

4.2.3 8.3 Multi-Agent Workflow

33

4.2.4 8.4 Compliance Scoring Algorithm

33

4.2.5 8.5 LLM Prompt Construction

34

4.3 Technology Stack

34

4.3.1 9.1 Development Technologies

34

4.3.2 9.2 Technology Justification

35

4.3.3 9.3 System Requirements

35

4.3.4 9.4 Deployment Architecture

36

5 RESULTS, DISCUSSIONS AND CONCLUSIONS

47

5.1 Results and Evaluation

47

5.1.1 Test Dataset

47

5.1.2 Performance Metrics

48

5.1.3 Processing Time Analysis

48

5.1.4 RAG Effectiveness

49

5.2 Novelty and Contributions

49

5.2.1 Key Innovations

50

5.2.2 Contribution Summary

51

5.2.3 Comparison with Existing Solutions

52

5.3 Future Enhancements

52

5.3.1 Short-term (3-6 months)

52

5.3.2 Medium-term (6-12 months)

53

5.3.3 Long-term (12+ months)

54

5.3.4 Research Extensions

54

5.4 Conclusion

55

5.4.1 Theoretical Contributions

55

5.4.2 Practical Achievements

56

5.4.3 Broader Impact

57

BIBLIOGRAPHY

58

LIST OF FIGURES

Figure No.

Caption

Page No.

3.1

High-Level System Architecture.

19

3.2

Three-Phase Processing Pipeline.

20

3.3

Component Class Diagram

20

3.4

Research Methodology Flowchart

21

4.1

7.1 Directory Structure Code 1

37

4.2

7.2.1 Document Parser Code 2.

38

4.3

7.2.2 Compliance Checker Code 3

38

4.4

7.2.3 RAG Knowledge Base Code 4

39

4.5

7.2.4 Agent Orchestrator Code 5.

39

4.6

ComplianceAPI Client Class (api.js) Code 6

39

4.7

Data Persistence Architecture

40

4.8

Processing Status State Machine

40

4.9

8.1 Document Processing Algorithm Code 1

41

4.10

RAG Retrieval Flowchart

42

4.11

Multi-Agent Workflow Sequence

43

4.12

8.4 Compliance Scoring Algorithm Code 4

43

4.13

LLM Prompt Construction Pipeline

44

4.14

Technology Stack Overview

45

5.1

Compliance Score Improvement Chart

48

5.2

Project Innovation Areas

50

LIST OF TABLES

Table No.

Caption

Page No.

2.1

Comparison of Previous Works in Privacy Policy Analysis

10

3.1

OPP-115 Compliance Categories.

23

3.2

Violation Severity Classification

23

4.1

7.3 API Endpoints Table 1

27

4.2

7.7 Multi-Format Export System Table 2

31

4.3

Technology Justification

46

5.1

Compliance Score Improvement Across Test Documents

47

5.2

Processing Time by Phase

48

5.3

RAG Effectiveness Comparison

49

5.4

Feature Comparison with Existing Solutions

52

GLOSSARY

Item

Description

RAG

Retrieval-Augmented Generation a technique that enhances LLM output by retrieving relevant documents from a knowledge base at inference time

LLM

Large Language Model a neural network trained on massive text corpora capable of understanding and generating natural language

NLP

Natural Language Processing a subfield of AI focused on enabling computers to understand and process human language

OPP-115

Online Privacy Policies 115 a benchmark dataset of 115 annotated privacy policies used for privacy policy research

GDPR

General Data Protection Regulation the EU regulation governing data protection and privacy

CCPA

California Consumer Privacy Act a California state statute enhancing consumer privacy rights

API

Application Programming Interface

CNN

Convolutional Neural Network

ANN

Approximate Nearest Neighbour a search technique for finding similar vectors in high-dimensional space

CRUD

Create, Read, Update, Delete the four basic operations of persistent storage

ETA

Estimated Time of Arrival used in the system for processing time prediction

MPA

Multi-Page Application a web architecture where each page is a separate HTML document

DNT

Do Not Track a W3C standard for browser privacy signals

DSR

Design Science Research a research methodology for building and evaluating IT artefacts

SME

Small and Medium-sized Enterprise

Chapter 1

INTRODUCTION

1.1 Background

In the digital age, the rapid growth of online services, mobile applications, and Internet of Things (IoT) devices has made it possible to collect, process, and share more personal data than ever before across organisational boundaries. Privacy policies are the fundamental legal instruments through which organisations inform end users about their data handling practices. These documents are more than mere informational disclosures; they are legally binding contracts that delineate the terms of data exchange between service providers and users.

The conceptual foundation of privacy policies rests upon the principle of "informed consent," which mandates that organisations must provide clear, complete, and comprehensible information about their personal data processing activities prior to data collection. This principle is enshrined in virtually every major privacy regulation worldwide, including the European Union's General Data Protection Regulation (GDPR), the California Consumer Privacy Act (CCPA) in the United States, Brazil's Lei Geral de Proteção de Dados (LGPD), Canada's Personal In- formation Protection and Electronic Documents Act (PIPEDA), and Singapore's Personal Data Protection Act (PDPA).

Despite their critical importance, privacy policies remain one of the most chal- lenging aspects of digital governance. According to a seminal study by McDonald and Cranor (2008), the average internet user would need approximately 244 hours per year to read all the privacy policies they encounter an expectation that is clearly impractical. Research consistently indicates that fewer than 10% of users read privacy policies prior to providing consent (Obar & Oeldorf-Hirsch, 2020). This creates a fundamental paradox: the documents designed to empower users with information about their data are largely unread and misunderstood.

From an organisational perspective, creating effective privacy policies presents several interconnected challenges:

• Regulatory Complexity: Privacy regulations vary significantly across ju- risdictions. The GDPR mandates specific rights such as data portability and the right to erasure, while the CCPA provides the right to opt out of data sales. Organisations operating globally must navigate a patchwork of sometimes conflicting regulatory requirements.

• Completeness and Comprehensiveness: Policies must address all neces- sary categories of data handling, including first-party data collection, third- party sharing, data retention schedules, security measures, and user access rights. Omitting any critical category can expose the organisation to legal liability.

• Clarity and Readability: Legal precision often renders policies incom- prehensible to the average user. Reidenberg et al. (2015) found consider- able ambiguity in privacy policy language that even legal experts could not consistently interpret, highlighting the tension between legal accuracy and readability.

• Currency and Maintenance: As organisational data practices evolve- through new product features, third-party integrations, or changes in data processing infrastructure privacy policies must be correspondingly updated. Many organisations fail to maintain current policies, leading to compliance drift.

Traditional approaches to creating and maintaining privacy policies each have significant limitations:

Manual drafting by legal teams: While producing the highest-quality output, manual drafting is costly (legal consultation fees ranging from $200 to $500 per hour), time-consuming (weeks to months for comprehensive poli- cies), and does not scale for organisations managing multiple products or jurisdictions.

Template-based generators: These tools offer speed and low cost but produce generic content that may not accurately represent an organisation's specific data practices, creating an illusion of compliance.

Consultant services: External consultants bring domain expertise but also create organisational dependency, are expensive, and may lack sufficient understanding of the organisation's technical infrastructure to produce truly accurate policies.

Compliance management platforms: Enterprise solutions such as One Trust and TrustArc provide structured compliance workflows but typically focus on policy management rather than policy content creation. Their high li- censing costs make them inaccessible to small and medium-sized enterprises (SMEs).

These limitations underscore the need for an automated, intelligent system that can analyse existing privacy policies, identify compliance gaps, and generate legally sound content to address those gaps. This project addresses that need.

1.2 Motivation

The motivation for this project stems from a convergence of regulatory, techno- logical, and market trends:

Increasing Regulatory Enforcement: Regulatory bodies worldwide have intensified their enforcement actions. GDPR fines can reach up to €20 mil- lion or 4% of global annual turnover, whichever is higher. By 2024, cumula- tive GDPR fines exceeded €4.5 billion. In 2021, Amazon incurred a record €746 million fine; in 2023, Meta was fined €1.2 billion. Under CCPA, similar enforcement trends are emerging, with penalties of up to $7,500 per inten- tional violation. This regulatory pressure makes compliance not merely a best practice but a financial necessity.

Growing User Privacy Awareness: Following high-profile data breaches (Equifax, 2017; Facebook-Cambridge Analytica, 2018; Marriott, 2018) and increasing media coverage of surveillance capitalism, public awareness of data privacy has surged. The Cisco 2023 Consumer Privacy Survey found that 92% of consumers consider data privacy a fundamental right, and 81% eval- uate companies based on their data protection practices. Clear and compre- hensive privacy policies are therefore essential for building and maintaining user trust.

Advances in NLP and Generative AI: The emergence of Large Language Models (LLMs) such as GPT-4, Llama, and Mistral has fundamentally trans- formed natural language processing. These models demonstrate remarkable capabilities in text understanding, generation, and reasoning that were not possible five years ago. When enhanced with domain-specific knowledge via Retrieval-Augmented Generation (RAG), LLMs can produce contextually relevant, factually grounded content that approximates human expert qual- ity.

SME Compliance Gap: While large enterprises can afford dedicated legal and compliance teams, small and medium-sized businesses which constitute over 90% of all businesses worldwide often lack the resources to create comprehensive privacy policies. An automated solution democratises access to compliance tools, enabling organisations of all sizes to maintain robust privacy practices.

Academic and Industry Need: Despite growing research in privacy policy analysis (Polisis, Policy Lint, PrivaSeer), few systems combine analysis with generation. The academic community has recognised this as a significant gap, with survey papers advocating for integrated compliance systems that go beyond classification to provide actionable remediation.

1.3 Scope

This project focuses on:

• Analysis of privacy policy documents in TXT, HTML, PDF, and DOCX formats

• Compliance checking against the OPP-115 privacy practice standard, which provides a well-established taxonomy of 10 privacy practice categories

• AI-powered generation of missing or incomplete policy sections using RAG- enhanced LLMS

• Multi-agent architecture for collaborative content generation with built-in quality assurance

Web-based interface for document upload, processing, and result visualisa- tion

1.4 Problem Statement

1.4.1 Problem Definition

The primary research question this project addresses is:

How can we develop an automated system that analyses privacy policy documents for compliance gaps against established standards and generates contextually ap- propriate, legally accurate remedial content using AI, while reducing hallucination and ensuring alignment with real-world privacy policy conventions?

This overarching problem decomposes into several interrelated sub-problems, each with distinct technical and domain-specific challenges:

Compliance Assessment Automation: Manual compliance checking is time-consuming (4-8 hours per policy), expensive, and inherently subjective, as different reviewers may interpret the same policy text differently. The challenge is to create a systematic, repeatable assessment framework that can evaluate policies against a standardised taxonomy (OPP-115) and produce consistent results.

Multi-Format Document Understanding: Privacy policies exist in vari- ous formats TXT, HTML, PDF, and DOCX each presenting unique pars- ing challenges. PDF files may have complex layouts, headers, footers, and non-text elements. HTML documents may contain navigation elements, scripts, and styles that obscure the actual policy content. The system must reliably extract meaningful text from all supported formats.

Grounded Content Generation: LLMs can produce fluent text but are also prone to "hallucination" generating plausible-sounding but factually incorrect or legally inappropriate content. In the compliance domain, this is particularly dangerous, as incorrect policy language could expose organ- isations to legal liability. The challenge is to ground generation in verified, real-world examples.

Preserving Original Intent: Unlike translation or summarisation tasks, compliance improvement requires augmenting a document without altering compliant content or the organisation's authentic voice. The system must distinguish between content that needs replacement, content that needs en- hancement, and content that should remain unchanged.

Integration Gap: Existing tools address isolated aspects of the compli- ance workflow either analysis or generation-but none provides a complete pipeline linking document parsing, compliance evaluation, and AI-powered remediation with quality assurance.

1.4.2 Challenges

Building an effective compliance automation system involves three interconnected areas of difficulty: regulatory, technical, and quality challenges.

Regulatory Challenges: Privacy regulations across the globe are not uniform and are constantly evolving. The GDPR alone comprises 99 articles and 173 recitals, and its interpretation continues to evolve through case law and regulatory guidance. Organisations operating across borders must simultaneously comply with multiple sometimes conflicting regulatory frameworks. Our system ad- dresses this by anchoring compliance evaluation to the OPP-115 standard, which captures universal categories present in most privacy regulations.

Technical Challenges: Processing natural language in legal documents requires understanding context, implicit references, and domain-specific terminology. For instance, "we may share your information" carries different compliance implica- tions depending on context sharing with service providers versus selling to ad- vertisers. Our system addresses this through keyword-based rule matching (for explicit mentions) combined with RAG-enhanced understanding (for contextual generation).

Quality Challenges: Generated content must meet high standards of accuracy, professionalism, and readability. Unlike creative writing or general-purpose text generation, errors in compliance content can have legal and financial consequences. Our multi-agent architecture addresses this by including a dedicated Reviewer Agent that validates generated content before inclusion in the final document.

Chapter 2

LITERATURE SURVEY AND OBJECTIVES

2.1 Literature Review

2.1.1 Privacy Policy Analysis

The field of automated privacy policy analysis has evolved substantially over the past decade, driven by advances in natural language processing and the growing volume of privacy regulations. Early approaches relied on manual annotation and basic keyword-based analysis, but as privacy policies grew in complexity and number, more sophisticated computational methods became necessary.

Foundational Work: The Usable Privacy Policy Project at Carnegie Mellon University represented the first organised effort to systematically analyse privacy policies. Sadeh et al. (2013) introduced the concept of automatically classifying segments of privacy policies into meaningful categories, laying the groundwork for subsequent machine learning approaches. Their research demonstrated that supervised learning could accurately identify different types of privacy practices within policy text.

Deep Learning Approaches: Harkous et al. (2018) unveiled Polisis, an inno- vative system that utilised deep learning to autonomously analyse and visualise privacy policies. Polisis employed a multi-label classifier based on Convolutional Neural Networks (CNNs) to categorise policy sentences into predefined groups, achieving approximately 88% Fl-score. However, Polisis remained fundamentally a classification system it could identify what a policy stated but could not suggest improvements or generate missing content.

Rule-Based and Hybrid Methods: PrivacyCheck (Zaeem & Barber, 2019) adopted a novel approach by integrating rule-based analysis with NLP techniques to evaluate privacy policies against a predetermined set of user enquiries regard- ing their data. PrivaSeer (Srinath et al., 2021) developed a privacy policy search engine using transformer-based models to classify and retrieve relevant policy segments. PolicyLint (Andow et al., 2020) focused specifically on contradiction detection using NLP techniques to identify inconsistencies within privacy poli- cies, such as conflicting claims about data usage. This work highlighted how common it is for real-world policies to be internally inconsistent, but offered no remediation capabilities.

LLM-Based Analysis: PolicyGPT (Tang et al., 2023) explored the use of LLMs for privacy policy understanding, demonstrating the potential of large language models for policy analysis. However, this approach lacked RAG grounding, making it susceptible to hallucination.

A comprehensive comparison of previous works is presented below:

Research Gap Identified: A significant deficiency in previous studies is the lack of a cohesive system that integrates compliance analysis with compliant content generation. Existing tools can identify problems in privacy policies but cannot fix them. Our system closes this gap by combining rule-based compliance checking with RAG-enhanced generative AI.

2.1.2 OPP-115 Dataset

The OPP-115 (Online Privacy Policies-115) dataset, presented by Wilson et al. (2016) at the 54th Annual Meeting of the Association for Computational Linguistics (ACL), serves as the predominant benchmark corpus for privacy pol- icy research. The dataset was created through a rigorous annotation process con- ducted by trained law school students.

Dataset Composition:

TABLE 2.1: Comparison of Previous Works in Privacy Policy Analysis

Study

Year

Approach

Key Contribution

Limitation

Sadeh et al.





Polisis (Harkous et al.)

2013





2018

Supervised ML classification



CNN-based deep learning multi-label classification

First automated policy categorisation



High accuracy classification

Limited categories, small dataset



No generation capability

PrivacyCheck (Zaeem & Barber)

2019

Hybrid rule-based + NLP

User question-focused analysis

Limited to specific question patterns

PolicyLint (Andow et al.)

2020

NLP contradiction detection

Finds policy inconsistencies

No improvement or remediation

PrivaSeer (Srinath et al.)

2021

Transformer-based search

Privacy policy search engine

Classification only, no remediation

PolicyGPT (Tang et al.)

2023

LLM-based analysis

LLM for policy understanding

No RAG grounding, risk of hallucination

115 privacy policies curated from major websites across various sectors (e-commerce, social media, healthcare, finance, technology, education)

23,000+ annotated data practice segments manually labelled by trained annotators

10 standardised privacy practice categories forming a comprehensive taxonomy of data practices

Inter-annotator agreement measured using Krippendorff's alpha at 0.72, in- dicating substantial agreement

Annotation Taxonomy: The 10 OPP-115 categories were designed to cover all aspects of data practices that a comprehensive privacy policy should address. Each category represents a distinct facet of the data lifecycle:

First Party Collection/Use: How the organisation collects and uses per- sonal data, including types of data collected, purposes of collection, and collection methods.

Third Party Sharing/Collection: Data sharing with external entities such as advertisers, analytics providers, and business partners.

User Access, Edit, and Deletion: User rights to access, modify, or delete their personal information.

Data Retention: Duration of personal data storage and criteria for deter- mining retention periods.

Data Security: Technical and organisational measures to protect personal data from unauthorised access, breaches, and loss.

Policy Change: How users are notified about changes to the privacy policy (e.g., email notification, website posting, opt-in requirement).

User Choice/Control: Opt-in/opt-out mechanisms and user consent op- tions.

Do Not Track: Organisational response to browser Do Not Track (DNT) signals, a W3C standard for communicating user privacy preferences.

International and Specific Audiences: Compliance for specific groups such as children under COPPA, international users under GDPR, and Cali- fornia residents under ССРА.

Other: Privacy-related practices not covered by the above categories (e.g., contact information, legal basis for processing).

Importance for This Project: The OPP-115 dataset serves two critical func- tions in our system: (1) it defines the compliance taxonomy against which input documents are evaluated, and (2) its 23,000+ annotated segments, grouped by category, constitute the core of our RAG knowledge base, providing real-world examples for grounded content generation.

2.1.3 Retrieval-Augmented Generation (RAG)

Lewis et al. (2020) introduced Retrieval-Augmented Generation (RAG) at NeurIPS. RAG addresses fundamental limitations of standalone Large Language Models by incorporating external knowledge retrieval at inference time. RAG has become one of the most important paradigms in modern NLP, transforming domain-specific AI applications.

Theoretical Foundation: RAG is grounded in the principle that generation quality improves when models have access to relevant, factual information during the generation process. Rather than directly modelling $P(y|x)$, where y is the output and  is the input, RAG models $P(y|x,z)$, where z represents retrieved documents:

$P(y|x)=\sum_{i}P(y|x,z_{i})\times P(z_{i}|x)$

(2.1)

where $z_{i}$ are documents retrieved from a knowledge base that are relevant to input . This decomposition allows the model to leverage external knowledge without encoding all information in its parameters.

RAG Architecture: The RAG pipeline comprises two complementary compo- nents:

Retriever Component: Responsible for finding relevant documents from a knowledge base. Our implementation uses dense retrieval with sentence- transformers (specifically the all-MiniLM-L6-v2 model) to embed both queries and documents into a shared 384-dimensional embedding space. Cosine sim- ilarity is used for semantic matching, which has been shown to outperform traditional sparse retrieval methods (TF-IDF, BM25) by capturing meaning rather than mere lexical overlap.

Generator Component: Takes the original input together with retrieved documents as context and produces the output. In our system, the Llama 3.1 model serves as the generator, creating privacy policy content grounded in real-world examples retrieved from the knowledge base.

Vector Databases and Embeddings: The retrieval process relies on vector embeddings dense numerical representations of text that capture semantic mean- ing. ChromaDB serves as our vector database, storing embeddings and enabling efficient approximate nearest neighbour (ANN) searches. The embedding model converts text into 384-dimensional vectors, with semantically similar texts mapped to proximate points in vector space.

Benefits of RAG over Fine-Tuning: While fine-tuning modifies an LLM's weights for a specific domain, RAG offers several advantages:

No retraining required: The knowledge base can be updated without model retraining

• Transparency: Retrieved sources can be inspected and cited, improving interpretability

Reduced hallucination: Generation is grounded in real documents rather than parametric memory alone

Cost-effective: Avoids the substantial computational cost of fine-tuning large models

• Data efficiency: Works effectively with small domain-specific corpora (our system uses 801 policy sections)

RAG addresses critical LLM limitations in the compliance context:

Hallucination: Grounds generated text in real privacy policy examples

• Knowledge Cutoff: Provides access to domain-specific privacy policy lan- guage and conventions

Domain Specificity: Enables generation of content matching the style, tone, and legal accuracy of real-world policies

2.1.4 Agentic AI and Multi-Agent Systems

Agentic AI represents a transformative shift from monolithic single-model archi- tectures to cooperative multi-agent systems, building upon decades of research in Multi-Agent Systems (MAS) within artificial intelligence.

Theoretical Background: The formal study of multi-agent systems commenced in the 1980s within the framework of Distributed Artificial Intelligence (DAI). Wooldridge and Jennings (1995) provided the seminal definition of a software agent as an autonomous entity that: (1) operates without direct human intervention, (2) is social by interacting with other agents, (3) is reactive by responding to environmental changes, and (4) is proactive by taking initiative to achieve goals. These properties remain fundamental to modern agentic AI systems.

LLM-Powered Agents: The emergence of powerful LLMs has enabled a new class of agent. Each agent is backed by an LLM with a specialised system prompt defining its role, capabilities, and behavioural constraints. Notable frameworks in this space include AutoGen (Wu et al., 2023), CrewAI, and LangGraph, which fa- cilitate the creation, coordination, and management of LLM-powered agent teams.

Agent Architectures: Modern agentic systems typically employ one of several architectural patterns:

Sequential Pipeline: Agents perform tasks in a fixed order (Agent A → Agent B→ Agent C). Our system follows this pattern, with Analyst, Gen- erator, and Reviewer agents processing each violation sequentially.

Hierarchical Delegation: A master agent delegates sub-tasks to specialist agents and aggregates their outputs.

Debate/Discussion: Multiple agents discuss and refine a solution, poten- tially reaching consensus through argumentation.

Collaborative Planning: Agents jointly decompose a complex task, with each agent responsible for a component.

Role Specialisation in Our System: Our multi-agent architecture employs three specialised roles:

• Analyst Agent: Reviews the compliance report, ranks violations by sever- ity and business impact, and creates a structured remediation plan-analogous to a compliance officer triaging issues.

Generator Agent: Receives prioritised violations and RAG-retrieved ex- amples to produce compliant content for each missing or inadequate section- functioning like a contract-drafting lawyer.

Reviewer Agent: Validates generated content for legal accuracy, com- pleteness, and stylistic consistency with the original document analogous to quality control in professional legal writing.

The Agent Orchestrator coordinates the workflow, ensuring smooth information flow between agents, handling error recovery and retries, and assembling the final output document.

2.1.5 Large Language Models for Legal Text

The application of Large Language Models to legal text processing represents a rapidly expanding research area at the intersection of NLP and legal informatics.

Evolution of Language Models:

Statistical models (n-grams, Hidden Markov Models): Captured local word co-occurrence patterns but lacked deep semantic understanding.

Word embeddings (Word2Vec, GloVe): Introduced distributed represen- tations capturing semantic relationships.

Transformer architecture (Vaswani et al., 2017): Introduced self-attention mechanisms enabling models to capture long-range dependencies in text.

Pre-trained language models (BERT, GPT): Demonstrated that large- scale pre-training on unlabelled text followed by task-specific fine-tuning achieves state-of-the-art performance across NLP benchmarks.

• Large Language Models (GPT-3/4, Llama, Mistral): Scaled transformer models with billions of parameters, demonstrating emergent capabilities in reasoning, instruction following, and few-shot learning.

Challenges in Legal NLP: Processing legal text is inherently more difficult than general-domain text due to:

• Domain-specific terminology: Legal documents contain specialised vo- cabulary with precise meanings that differ from everyday usage.

• Long document context: Privacy policies and legal contracts often span thousands of words, requiring models with large context windows.

Precision requirements: Legal text demands accuracy and precision far exceeding general text generation, as errors can lead to legal liability.

• Multi-jurisdictional interpretation: The same concepts may be expressed differently across legal systems, requiring models capable of handling cross- jurisdictional variation.

We selected Meta's Llama 3.1 as our LLM for this project based on its strong performance on legal and compliance text benchmarks, its open-source nature en- abling local deployment, and its 128K token context windowsufficient to handle complete privacy policy documents with RAG context. Local deployment via Ol- lama ensures complete data privacy, which is essential when processing potentially sensitive policy documents.

2.2 Objectives

2.2.1 Primary Objectives

Develop a document parsing system capable of extracting text from multiple formats (TXT, HTML, PDF, DOCX)

Implement a compliance checking engine that validates documents against OPP-115 privacy practice categories

Build a RAG-enhanced AI generation system that creates compliant policy sections grounded in real examples

Create a web-based user interface for document upload, processing, and result visualisation

2.2.2 Secondary Objectives

Enable batch processing of multiple documents simultaneously

Generate comprehensive compliance reports with violation severity levels

Support local LLM deployment for privacy-sensitive processing

Provide containerised deployment via Docker

2.2.3 Extended Objectives (Recently Completed)

Multi-format document export supporting PDF, HTML, and plain text downloads

Custom compliance rules engine allowing users to define keyword-based rules with severity levels

System analytics dashboard with processing trends, compliance distri- bution charts, and score history

Side-by-side document comparison with synchronised scrolling and gen- erated section highlighting

Processing ETA and activity logging with real-time progress tracking and state persistence

Chapter 3

RESEARCH

METHODOLOGY

3.1 System Architecture

3.1.1 High-Level Architecture

The system follows a layered architecture design with clear separation of con- cerns. The five layers Frontend, API, Processing, AI, and Storage communicate through well-defined interfaces, enabling independent development and testing of each component.

3.1.2 Three-Phase Processing Pipeline

The core of the system is a sequential three-phase pipeline. Each phase produces structured outputs that feed into the next phase, ensuring a clean flow from raw document input to improved, compliant output.

3.1.3 Component Diagram

The system's object-oriented design comprises several interconnected classes, each with clearly defined responsibilities:

Frontend Layer API Layer Processing Layer AI Layer Storage Layer [Image: FIGURE 3.1: High-Level System Architecture]

3.2 Methodology

3.2.1 Research Methodology

This project employs an Iterative Development Methodology in conjunc- tion with Design Science Research (DSR), a research framework established by Hevner et al. (2004) that is particularly well-suited for information systems research involving the creation of novel artefacts. DSR focuses on building and evaluating IT artefacts (constructs, models, methods, and instantiations) designed to address identified organisational problems.

The DSR framework is especially appropriate for this project because it:

• Develops a novel IT artefact (the compliance automation system) to address a recognised problem (privacy policy compliance gaps)

Phase 1: Parsing Phase 2: Compliance Phase 3: AI Generation [Image: FIGURE 3.2: Three-Phase Processing Pipeline]

DocumentParser +parse_document (file) +detect_format() +extract_text() +extract_metadata() Analyst Agent +analyze_violations() +prioritize_gaps() ComplianceChecker +check_document(doc) +load_rules() +detect_violations() calculate_score() Generator Agent +generate_section() +apply_template() Agent Orchestrator +process_document() +coordinate_agents() +-manage_workflow() Reviewer Agent +review_content() +validate_compliance() RAGKnowledge Base +add_documents() +similarity_search() +get_relevant_examples() LLMInterface +generate() +chat() +embed() [Image: FIGURE 3.3: Component Class Diagram]

• Requires rigorous evaluation against established benchmarks (OPP-115 com- pliance standards)

• Provides both practical utility (a functioning system) and academic contri- butions (insights into RAG-enhanced legal text generation)

The iterative development process follows a modified Agile methodology with short development cycles focused on each pipeline phase, continuous integration testing, and iterative refinement based on evaluation results:

Problem Identification Literature Review Solution Design Implementation Evaluation No Satisfactory? Yes Documentation [Image: FIGURE 3.4: Research Methodology Flowchart]

Phase 1 (Document Parsing) was developed and tested first, followed by Phase 2 (Compliance Checking), and finally Phase 3 (AI Generation). This incremen- tal approach ensured that each component was robust before adding the next, minimising cascading errors.

3.2.2 Data Collection and Knowledge Base Construction

Primary Dataset: The OPP-115 dataset serves as both the evaluation bench- mark and the knowledge source:

115 privacy policies from major websites across diverse industries

23,000+ professionally annotated segments

10 standardised categories covering all aspects of privacy practices

Annotations performed by trained law school students with inter-annotator agreement of 0.72 (Krippendorff's alpha), indicating substantial reliability

Knowledge Base Construction Pipeline: Building the RAG knowledge base is a critical preprocessing step that transforms raw OPP-115 annotations into a semantically searchable vector database. The pipeline comprises four stages:

Data Extraction and Cleaning: Raw policy segments are extracted from OPP-115 annotation files. Each segment undergoes cleaning to re- move HTML artefacts, normalise whitespace, and filter out segments that are too short (fewer than 20 characters) or too noisy to serve as generation references. This yields 801 high-quality policy sections.

Semantic Embedding: The all-MiniLM-L6-v2 sentence-transformer model converts each cleaned segment into a dense 384-dimensional vector represen- tation (embedding) that captures the semantic meaning of the text. This model was selected for its optimal balance between embedding quality and computational efficiency significantly faster than larger models while main- taining strong semantic similarity performance (Spearman correlation of 0.84 on the STS benchmark).

Vector Storage in ChromaDB: ChromaDB, a lightweight open-source vector database, stores the embeddings alongside their text content and metadata (category label, source policy, segment ID). ChromaDB was cho- sen for its in-process architecture (no external database server required), Python-native API, and support for metadata-filtered similarity search.

Category-Based Indexing: Each embedded segment retains its OPP-115 category label as metadata, enabling category-scoped retrieval. When the system needs to generate content for a missing "Data Security" section, it constrains its search to segments tagged with that category, ensuring domain- relevant results.

3.2.3 Compliance Categories

The system evaluates policies against 10 OPP-115 categories:

TABLE 3.1: OPP-115 Compliance Categories

Category

Description

Mandatory

First Party Collection/Use

How the service collects user data

Yes

Third Party Sharing/Collection

Data sharing with external parties

Yes

User Access, Edit and Deletion

User rights to manage their data

Yes

Data Retention

How long data is stored

Yes

Data Security

Protection measures

Yes

Policy Change

How changes are communicated

Yes

User Choice/Control

User options and consent

Yes

Do Not Track

Response to DNT signals

No

International and Specific Audiences

COPPA, international users

No

Other

Miscellaneous practices

No

3.2.4 Violation Severity Levels

The system classifies violations into four severity levels to prioritise remediation efforts:

TABLE 3.2: Violation Severity Classification

Severity

Description

Example

CRITICAL

Missing mandatory section entirely

No Data Security section

HIGH

Major compliance gap in a mandatory category

Incomplete third-party sharing disclosure

MEDIUM

Recommended practice missing or insufficient

No specific data retention period stated

LOW

Minor improvement suggestion

Clarity or readability enhancement

Mandatory categories (First Party Collection, Third Party Sharing, User Access, Data Retention, Data Security, Policy Change, User Choice/Control) carry higher weights in the compliance score calculation, reflecting their regulatory importance. Missing mandatory sections receive a CRITICAL severity rating, while optional categories (Do Not Track, International and Specific Audiences, Other) receive lower severity ratings when absent.

Chapter 4

ACTUAL WORK

4.1 Implementation Details

This chapter presents the complete implementation of the Compliance Automation System, covering the project structure, core components, API design, frontend architecture, and the algorithms that drive the compliance analysis pipeline. Each subsection provides detailed technical descriptions and code excerpts illustrating how the three-phase processing pipeline was realised in practice.

4.1.1 7.1 Directory Structure

The project follows a clean separation of concerns with three top-level directories: backend for the Flask API server, frontend for the multi-page web interface, and src for the core processing logic. This modular organisation enables independent development and testing of each layer, and simplifies containerised deployment via Docker.

4.1.2 7.2 Key Implementation Components

The system is built around four core classes that together implement the three- phase processing pipeline. Each class encapsulates a distinct responsibility- parsing, checking, retrieval, and orchestration allowing loose coupling and clear interfaces between components. The following subsections present the key class interfaces along with their input/output contracts.

4.1.2.1 7.2.1 Document Parser

The DocumentParser class provides format-agnostic document ingestion, support- ing TXT, HTML, PDF, and DOCX files. It uses format-specific libraries (Beauti- fulSoup4 for HTML, PyPDF2 for PDF, python-docx for DOCX) to extract both textual content and structural metadata, producing a standardised dictionary that downstream components can consume regardless of the original file format.

4.1.2.2 7.2.2 Compliance Checker

The ComplianceChecker implements a rule-based validation engine that evaluates parsed documents against all ten OPP-115 privacy practice categories. For each category, the checker calculates a coverage score based on keyword matching and contextual analysis, flags violations when coverage falls below configurable thresh- olds, and assigns a severity level (Critical, High, Medium, or Low) based on the category's regulatory importance.

4.1.2.3 7.2.3 RAG Knowledge Base

The RAGKnowledgeBase class manages the vector database of 801 real privacy pol- icy sections extracted from the OPP-115 dataset. It uses the all-MiniLM-L6-v2 sentence transformer model to encode both stored sections and incoming queries into a shared 384-dimensional embedding space. Category-scoped similarity search ensures that retrieved examples are relevant to the specific violation being ad- dressed, providing the LLM with contextually appropriate grounding material.

4.1.2.4 7.2.4 Agent Orchestrator

The AgentOrchestrator coordinates the multi-agent workflow that transforms compliance violations into improved document content. It manages three spe- cialist agents Analyst, Generator, and Reviewer and implements the iterative generate-review-revise loop. The orchestrator prioritises violations by severity, en- suring that the most critical compliance gaps are addressed first, and assembles the final improved document by merging generated content with preserved compliant sections.

4.1.3 7.3 API Endpoints

The Flask backend exposes a RESTful API with over 25 endpoints organised into five functional groups: document management (upload, list, delete, download), processing control (start, status, ETA), reporting (compliance reports, export), analytics (statistics, trends), and configuration (custom rules, health check). All endpoints return JSON responses and use standard HTTP status codes, enabling straightforward integration with the frontend JavaScript client.

4.1.4 7.4 Frontend Architecture

The frontend is a multi-page application (MPA) consisting of 7 distinct pages, each with dedicated JavaScript modules. All pages share a common design system through main.css and dashboard.css, using a dark theme with accent colors and glassmorphism effects.

4.1.4.1 7.4.1 Dashboard (index.html)

The main landing page displays:

API connection status indicator (healthy/disconnected)

• Summary statistics cards: total documents, completed, average compli- ance score, currently processing

Document table with status badges, phase indicators, timestamps, and contextual action buttons (Process, View, Report, Compare, Delete)

Auto-refresh every 5 seconds for real-time status updates without page reload

TABLE 4.1: 7.3 API Endpoints Table 1

Endpoint

Method

Description

/api/health

GET

System health check

/api/upload

POST

Upload document (supports batch)

/api/process/<id>

POST

Start processing a document

/api/status/<id> 



 /api/report/<id>

GET 



 GET

Get processing status with ETA 



 Get compliance report

/api/document/<id>

GET

Get improved document text

/api/document/<id>

DELETE

Delete document and all related files

/api/compare/<id>

GET

Get before/after comparison data

/api/download_pdf/<id>

GET

Download improved document as PDF

/api/download/<id>

GET

Download improved document as text file

/api/download_html/<id>

GET

Download improved document as styled HTML

/api/statistics

GET

System statistics with score history

/api/documents

GET

List all documents with status

/api/process_dataset

POST

Process full OPP-115 dataset

/api/dataset_status

GET

Batch dataset processing status

/api/dataset_results

GET

Detailed results of dataset processing

/api/rules

GET

Get all custom compliance rules

/api/rules

POST

Save/update custom compliance rules

4.1.4.2 7.4.2 Upload Page (upload.html)

• Drag-and-drop file upload area with visual feedback

Batch upload support: select multiple files and upload them all sequentially

File validation with supported format display (TXT, HTML, PDF, DOCX) and 16MB size limit

File list management for batch uploads: individual file removal, clear all, file count display

• Upload progress bar with percentage indicator

• Success/error states with contextual action buttons

4.1.4.3 7.4.3 Processing Page (processing.html)

Real-time status polling with automatic phase timeline updates ETA estimation based on elapsed time and current phase progress

• Activity log with timestamped entries showing each processing step

State persistence using sessionStorage survives page refreshes and tab switches

• Tab visibility handling pauses/resumes polling when the user switches browser tabs

• Three-phase progress visualization (Parse -> Check -> Generate)

4.1.4.4 7.4.4 Report Page (report.html)

• Animated compliance score circle with SVG gradient rendering

• Summary statistics for critical, high, and medium priority violations and sections generated

• Violation list with severity filtering dropdown (All/Critical/High/Medium/Low)

• Category coverage chart using Chart.js bar chart

Multi-format export dropdown with PDF, HTML, and plain text down- load options

Link to side-by-side comparison view

4.1.4.5 7.4.5 Analytics Page (analytics.html)

• Overall stats cards: total processed, average compliance, success rate, violations fixed

. OPP-115 Full Dataset Processing: one-click processing of all 115 privacy policies with real-time progress bar, completion/failure counters, and current document indication

• Processing Status doughnut chart (completed vs. processing vs. failed)

• Compliance Distribution chart per document

• Compliance Score Trend line chart tracking the last 20 documents over time

Recent Activity table with document names, statuses, scores, and times- tamps

System Information panel showing LLM model, RAG knowledge base size, processing phases

Performance Metrics panel with average/fastest/total processing times

4.1.4.6 7.4.6 Comparison Page (compare.html)

• Side-by-side view of original vs. improved document

• Synchronized scrolling between original and improved panels

• Generated section highlighting - AI-generated sections are visually dis- tinguished

Stats showing sections added, compliance score before improvement, and improvement percentage

Download buttons for PDF and text export directly from the comparison view

4.1.4.7 7.4.7 Custom Rules Page (rules.html)

• CRUD interface for custom compliance rules

. Modal-based form for adding/editing rules with fields: name, category, keywords, severity, description

• Category selector with all 10 OPP-115 categories plus a custom category option

• Keyword-based rule matching with comma-separated input

• Severity assignment (Critical/High/Medium/Low) with color-coded badges

Rules count display and empty state placeholder

4.1.5 7.5 Shared Frontend Utilities

4.1.5.1 ComplianceAPI Client Class (api.js)

A centralized API client class encapsulating all backend communication:

Helper functions:

• formatDate() - Relative time formatting ("Just now", "5 minutes ago", etc.)

• getStatusBadge () - Status-specific colored badges

showToast() - Non-blocking notification system with auto-dismiss

4.1.6 7.6 Data Persistence

The backend implements JSON-based file persistence for processing data:

Data is loaded from disk on startup and saved on shutdown using atexit handlers

Automatic save after each document processing completion (success or fail- ure)

Thread-safe access using threading. Lock for concurrent processing

4.1.7 7.7 Multi-Format Export System

The report page provides a unified dropdown menu for exporting improved docu- ments in three formats:

TABLE 4.2: 7.7 Multi-Format Export System Table 2

Format

Description

PDF

Generated using ReportLab with formatted sections and compliance branding

HTML

Styled HTML with gradient header, compliance score, and professional layout

Text

Plain text download of the improved document content

The HTML export generates a self-contained, printable document with:

• Gradient header with document title and compliance score

• Georgia serif font for professional readability

White content card with box shadow and rounded corners

Footer branding with "Generated by Compliance AI RAG-Enhanced Gen- eration"

4.1.8 7.8 Batch Processing

Two levels of batch processing are supported:

Client-Side Batch Upload: Users can drag-and-drop or select multiple files. Files are uploaded and processed sequentially with individual progress tracking.

Full OPP-115 Dataset Processing: A dedicated feature on the Analytics page processes all 115 privacy policies from the OPP-115 dataset in a single background thread. Features include:

• Real-time progress bar with percentage

• Current/completed/failed document counters Current document name display

• Summary saved to outputs/full_dataset_processing_summary.json

4.1.9 7.9 Processing Status & ETA Estimation

The processing pipeline provides granular status updates:

ETA estimation uses:

• Elapsed time since processing started

Current phase (1-3) to estimate overall progress percentage

• Proportional calculation: remaining progress%)

elapsed / (progress%) * (100%

Fallback estimate based on file size $(\sim100~bytes/second)$

4.2 Algorithms and Flowcharts

This section formalises the key algorithms and workflows that power the Compli- ance Automation System. Pseudocode is provided for the main processing pipeline, while flowcharts and sequence diagrams illustrate the RAG retrieval process, multi- agent coordination, and LLM prompt construction.

4.2.1 8.1 Document Processing Algorithm

The core document processing algorithm implements the three-phase pipeline. Phase 1 handles format detection and text extraction, Phase 2 performs rule- based compliance checking against all OPP-115 categories, and Phase 3 triggers RAG-enhanced AI generation for any violations exceeding the severity threshold. The algorithm is designed to be fault-tolerant: if any phase encounters an error, the processing status is updated to "failed" with a descriptive error message, and partial results are preserved for debugging.

4.2.2 8.2 RAG Retrieval Flowchart

The RAG retrieval algorithm is triggered for each violation detected during Phase 2. Given a violation and its associated OPP-115 category, the algorithm constructs a search query, encodes it into a 384-dimensional vector using the all-MiniLM-L6-v2 model, and performs a category-scoped similarity search against the ChromaDB vector database. If matching examples are found, they are ranked by cosine simi- larity and the top k results (default $k=5$) are formatted as contextual examples for the LLM prompt. If no examples are found for the specified category, a default template is used as a fallback.

4.2.3 8.3 Multi-Agent Workflow

The multi-agent workflow implements a collaborative pattern inspired by profes- sional legal drafting teams. The Orchestrator coordinates three specialist agents in a structured sequence for each violation: (1) the Analyst Agent prioritises violations by severity and regulatory importance, (2) the Generator Agent pro- duces compliant content using RAG-retrieved examples as context, and (3) the Reviewer Agent validates the generated content for legal accuracy, style consis- tency, and OPP-115 coverage. If the reviewer rejects a draft, the loop repeats with refinement feedback. This separation of concerns mirrors the analyse-draft-review cycle used in real legal teams and improves output quality compared to single-pass generation.

The time complexity of the workflow is $O(v\times(r+g+w))$, where v is the number of violations, r is retrieval time, g is generation time, and w is review time. In practice, LLM inference (g) dominates, taking 15-30 seconds per violation on consumer hardware.

4.2.4 8.4 Compliance Scoring Algorithm

The compliance score provides a single quantitative metric summarising a docu- ment's overall compliance posture. The algorithm uses a weighted scoring model where mandatory OPP-115 categories (e.g., First Party Collection/Use, Data Re- tention) receive higher weights $(w_{m}=15)$ than optional categories $(w_{o}=5$, re- flecting their regulatory importance. The score is calculated as:

Compliance Score =

Σ 1 Wi

× 100

(4.1)

where $w_{i}$ is the weight of category i and $c_{i}\in[0,1]$ is the coverage score for that category, determined by keyword density and section detection analysis. The resulting score ranges from 0 (no compliance) to 100 (full compliance).

4.2.5 8.5 LLM Prompt Construction

Effective prompt engineering is essential for generating high-quality, legally ap- propriate content. The prompt construction pipeline assembles five components into a structured prompt: (1) a system prompt establishing the LLM's role as a privacy policy expert, (2) a task description specifying the violation category and required remediation, (3) example sections retrieved via RAG to provide grounding, (4) formatting requirements ensuring consistent output structure, and (5) an output format specification constraining the response. The prompt template uses Jinja2-style variable interpolation, allowing the system to dynami- cally inject violation-specific and category-specific content.

The following diagram illustrates how inputs from the violation analysis and RAG retrieval stages are combined through the template to produce the final prompt sent to Ollama's Llama 3.1 model.

4.3 Technology Stack

This section documents the technology choices made during the design and imple- mentation of the Compliance Automation System. Each technology was selected based on criteria including ecosystem maturity, privacy preservation, performance characteristics, and ease of deployment.

4.3.1 9.1 Development Technologies

The technology stack spans five domains: frontend presentation, backend API, AI/ML inference, document processing, and DevOps infrastructure. The following mindmap provides a visual overview of all technologies used in the project, followed by detailed justifications for each choice.

4.3.2 9.2 Technology Justification

Each technology in the stack was selected to satisfy specific project requirements. The following table summarises the primary purpose and selection rationale for each key technology:

Key Design Decision - Local LLM vs. Cloud API: A critical architectural decision was the use of Ollama for local LLM inference rather than cloud-based APIs such as OpenAI GPT-4 or Anthropic Claude. This decision was driven by three factors: (1) Privacy: privacy policy documents often contain sensitive or- ganisational information that should not be transmitted to third-party servers; (2) Cost: cloud API costs scale linearly with usage, whereas local deployment has a fixed infrastructure cost; (3) Reproducibility: local models produce determin- istic outputs with consistent temperature settings, enabling reliable testing and evaluation.

4.3.3 9.3 System Requirements

The system has been tested on both consumer-grade laptops and server-class hard- ware. The following tables specify the minimum and recommended configurations:

Minimum Requirements:

CPU: 4 cores (Intel i5 / AMD Ryzen 5 or equivalent)

RAM: 8 GB (sufficient for embedding model and small documents)

• Storage: 20 GB (includes model weights, vector database, and processed documents)

OS: Windows $10/11$, Ubuntu 20.04+, or macOS 12+

Software: Python 3.11+, Ollama 0.1.17+, Docker 24.0+ (optional)

Recommended Requirements (for production use):

CPU: 8+ cores (Intel $i7/i9$ or AMD Ryzen $7/9$

RAM: 16+ GB (required for Llama 3.1 8B model fully loaded in memory)

GPU: NVIDIA RTX 3060+ with 8GB+ VRAM (optional; enables 3-5x faster LLM inference)

• Storage: 50 GB SSD (fast $1/O$ for vector database queries and document processing)

Network: Not required for core functionality; needed only for initial setup (downloading model weights and Python packages)

4.3.4 9.4 Deployment Architecture

The system supports two deployment modes:

Development Mode: Direct execution using python app.py for the Flask backend and opening index.html in a browser for the frontend. This mode is suitable for development and testing, with Flask's built-in server handling requests on port 5000.

Production Mode (Docker): Multi-container deployment using Docker Compose with three services:

backend: Python 3.11 container running the Flask API with Gunicorn WSGI server

frontend: NGINX container serving static files and proxying API re- quests to the backend

ollama: Ollama container with the Llama 3.1 model pre-loaded for GPU-accelerated inference

The Docker Compose configuration ensures all three services are connected via an internal bridge network, with only the NGINX port (80) exposed externally. Vol- ume mounts persist processed documents and the vector database across container restarts.

[Image: FIGURE 4.1: 7.1 Directory Structure Code 1]

compliance/

backend/

app.py

requirements.txt

data/

#Flask API Server

#Main API with 25+ endpoints
#Backend dependencies

#Persistent storage (JSON-based)

processing_status.json # Processing state persistence

processing_results.json # Results persistence

#User-defined rules

#Web Interface

#Dashboard with real-time stats

#Document upload (single & batch)
#Live processing status with ETA

# Compliance report with export

custom_rules.json

uploads/

#Document uploads

frontend/

index.html

upload.html

processing.html

report.html

analytics.html

compare.html

rules.html

css/

js/

src/

main.css

dashboard.css

api.js

dashboard.js

upload.js

processing.js

report.js

analytics.js
compare.js

rules.js

nginx.conf

document_parser.py

data_loader.py

text_extractor.py

#System analytics & dataset processing

#Side-by-side document comparison
#Custom compliance rules manager

#Stylesheets

#Global styles & design system
#Dashboard-specific styles

#JavaScript modules

#API client class & utilities
#Dashboard logic with auto-refresh

#Upload with drag-drop & batch
#Live status polling with ETA

#Report display & export dropdown

# Charts & dataset processing

#Comparison with sync scrolling
#Custom rules CRUD operations

# NGINX configuration

#Core Processing Logic
#Format-agnostic parsing
#OPP-115 data loading

#Text extraction utilities.

metadata_extractor.py # Metadata parsing

utils.py

phase2/

#Shared utilities

#Compliance Checking

compliance_checker.py

rule_base.py

rule_engine.py

validators.py

phase3/

#AI Generation

orchestrator.py #Multi-agent coordinator

agents.py

#Specialist agents

llm_interface.py

#Ollama integration

rag_knowledge_base.py

prompt_templates.py

document_generator.py

pdf_generator.py

rules/

# Compliance Rules

opp115_rules.json

rule_templates.json

data/

#Data Storage

raw/

#OPP-115 dataset

processed/

rag_db/

# Intermediate data

#Vector database

config.py

convert_to_html.py

Dockerfile

docker-compose.yml

requirements.txt

#Central configuration

#Markdown-to-HTML converter with Mermaid

#Container definition

#Multi-container setup

#All dependencies.


[Image: FIGURE 4.2: 7.2.1 Document Parser Code 2]

class DocumentParser:

Multi-format document parser with metadata extraction"""

SUPPORTED_FORMATS

[.txt, html, pdf, .docx

def parse_document(self, file_path):

Parse document and return structured representation

Returns:

{

Filename: str,

text': str,

'metadata': {

word_count: int,

section count': int,

'detected categories': list

}

}


[Image: FIGURE 4.3: 7.2.2 Compliance Checker Code 3]

class Compliance Checker:

Rule-based compliance validation engine"""

def check_document(self, document):

Check document against OPP-115 categories

Returns:

{

'summary': {

compliance_score': float, #0-100

total violations': int,

'critical_count': int,

'high_count': int

},

'violations': [

{

'category': str,

}

1.

}

'severity': str,

message: str

'recommendation': str

category_coverage': dict


[Image: FIGURE 4.4: 7.2.3 RAG Knowledge Base Code 4]

class RAGKnowledge Base:

***Vector-based knowledge retrieval for policy examples"""

def __init__(self):

self.embedder SentenceTransformer('all-MiniLM-L6-v21)
self.db chromadb. Client()

self.collection  self.db.get_or_create_collection('policy_sections")

def similarity_search(self, query, category, k=5):

Find similar policy sections for a given category

Args:

query: Search query or violation description
category: OPP-115 category to search within
k: Number of results to return

Returns:

List of similar policy section texts


[Image: FIGURE 4.5: 7.2.4 Agent Orchestrator Code 5]

class AgentOrchestrator:

***Coordinates multi-agent workflow for document improvement***

def process_document(self, document, compliance_report):

Orchestrate agents to generate improved document

Workflow:

1. Analyst identifies priority violations

2. For each violation:

a. RAG retrieves relevant examples

b. Generator creates compliant content

c. Reviewer validates output

3. Assemble final document


[Image: FIGURE 4.6: ComplianceAPI Client Class (api.js) Code 6]

class ComplianceAPI {

}

checkHealth()

uploadDocument (file)

// Health check

// Upload with FormData

// Poll status with ETA

processDocument (docId) // Start processing

getStatus(docId)

getReport (docId)

getDocument (docId)

getComparison (docId)

getStatistics()

list Documents()
delete Document (docId)

// Fetch compliance report

// Get improved document

// Get comparison data

// System-wide stats

// List all documents

// Delete document

downloadDocument (docId) // Download as text
downloadPdf (docId)

// Download as PDF


[Image: FIGURE 4.7: Data Persistence Architecture] In-Memory Storage Persistent Storage Load/Save Load/Save

[Image: FIGURE 4.8: Processing Status State Machine] File uploaded Start Phase 1 uploaded parsing checking Error Phase 2 Phase 3 failed generating

[Image: FIGURE 4.9: 8.1 Document Processing Algorithm Code 1]

Algorithm: Process Document

Input: document_file

Output: improved_document, compliance_report

BEGIN

// Phase 1: Parsing

text <- ExtractText(document_file)

metadata< ExtractMetadata (document_file)

parsed_doc < CreateStructured Document(text, metadata)

// Phase 2: Compliance Checking

rules Load Compliance Rules ()

violations < []

FOR EACH category IN OPP115 CATEGORIES DO

coverage <- CheckCategoryCoverage (parsed_doc, category)
IF coverage < THRESHOLD THEN

violation <- CreateViolation (category, coverage)
violations. APPEND (violation)

END IF

END FOR

compliance_report << GenerateReport (violations)

// Phase 3: AI Generation

IF

HasCriticalViolations (violations) THEN

FOR EACH violation IN GetCriticalViolations (violations) DO

examples < RAG_Search (violation.category, k=5
prompt << ConstructPrompt (violation, examples)
generated_section < LLM_Generate (prompt)

reviewed_section < ReviewAgent. Review (generated_section)
AddSection(improved_document, reviewed_section)

END FOR

END IF

RETURN improved_document, compliance_report

END


[Image: FIGURE 4.10: RAG Retrieval Flowchart] Violation Detected Extract Category Create Search Query Embed Query Vector Search ChromaDB Yes Results Found? No Rank by Similarity Select Top K Format as Context Return to Generator Use Default Template

[Image: FIGURE 4.11: Multi-Agent Workflow Sequence] Orchestrator Analyst RAG System Generator Reviewer LLM Analyse report Priority violations loop: For each violation Search examples Relevant sections Generate with context Assemble final document Draft section Review draft Approved/Revise Prompt + examples Generated content Validate Feedback

[Image: FIGURE 4.12: 8.4 Compliance Scoring Algorithm Code 4]

Algorithm: CalculateComplianceScore

Input: document, category_results

Output: compliance_score (0-100)

BEGIN

total_weight <- 0

achieved_weight <- ()

FOR EACH category IN OPP115 CATEGORIES DO

IF category. mandatory THEN

ELSE

weight < 15 // Higher weight for mandatory

weight <- 5

END IF

// Lower weight for optional

total_weight << total_weight + weight

coverage <- category_results [category].coverage
achieved_weight

END FOR

achieved_weight + (weight coverage)

compliance_score < (achieved_weight / total_weight)  100

RETURN ROUND(compliance_score, 2)

END


[Image: FIGURE 4.13: LLM Prompt Construction Pipeline] Inputs Template Output

[Image: FIGURE 4.14: Technology Stack Overview] Docker ReportLab python-docx BeautifulSoup4 Docker Compose Git DevOps Doc Processing ChromaDB HTML5 Frontend CSS3 Technology Stack AI / ML sentence-transformers Llama 3.1 Backend JavaScript ES6+ Chart.js Flask-CORS Python 3.11 Flask 3.0 Ollama

TABLE 4.3: Technology Justification

Technology

Purpose

Why Chosen

Python 3.11

Backend development

Rich NLP ecosystem (NLTK, spaCy, transformers), rapid prototyping, strong community support

Flask 3.0

Web framework

Lightweight microframework; easy to extend with blueprints; minimal boilerplate compared to Django

Ollama + Llama 3.1

LLM inference

Local deployment ensures document data never leaves the organisation; zero API costs; 8B parameter model achieves strong performance on legal text

ChromaDB

Vector database

In-process embedded database; no external server required; native Python integration; efficient cosine similarity search

sentence-transformers

Text embeddings

Pre-trained model all-MiniLM-L6-v2 produces high-quality 384-dimensional embeddings; 5x faster than BERT-base with comparable accuracy

BeautifulSoup4

HTML parsing

Industry-standard HTML/XML parser; handles malformed markup gracefully; integrates with Python's built-in parsers

python-docx

DOCX processing

Read/write Microsoft Word documents natively; paragraph-level access for structured extraction

ReportLab

PDF generation

Programmatic PDF creation with headers, footers, and compliance branding; no external tool dependency

Chart.js 4.x

Data visualisation

Canvas-based responsive charts; supports doughnut, bar, line, and trend charts; lightweight (<200KB)

Docker

Containerisation

Consistent deployment across environments; NGINX reverse proxy for production; multi-container orchestration via Compose

Chapter 5

RESULTS, DISCUSSIONS AND CONCLUSIONS

5.1 Results and Evaluation

5.1.1 Test Dataset

Testing was performed on 10 sample privacy policies with varying levels of compli- ance. Each policy was processed through the complete three-phase pipeline, and compliance scores were measured before and after AI-powered content generation:

TABLE 5.1: Compliance Score Improvement Across Test Documents

Document

Initial Score

Final Score

Improvement

TechStart Policy

45.2%

87.3%

+42.1%

ShopEasy Policy

52.1%

89.5%

+37.4%

Health Track Policy

38.7%

85.2%

+46.5%

CloudDocs Policy

61.3%

92.1%

+30.8%

GameZone Policy

55.8%

88.7%

+32.9%

EduLearn Policy

42.5%

86.4%

+43.9%

FoodieApp Policy

48.9%

90.2%

+41.3%

SecureBank Policy

71.2%

95.8%

+24.6%

SmartHome Policy

63.4%

91.5%

+28.1%

TravelBuddy Policy

57.6%

89.8%

+32.2%

Average

53.7%

89.7%

+36.0%

The results demonstrate consistent compliance improvement across all test doc- uments, with an average improvement of 36 percentage points. Documents with lower initial scores (e.g., Health Track at 38.7%) showed the greatest improvement, as they had more missing sections for the system to generate. Documents with higher initial scores (e.g., Secure Bank at 71.2%) showed smaller but still signif- icant improvements, primarily through enhancement of existing sections rather than generation of entirely new ones.

5.1.2 Performance Metrics

[Image: FIGURE 5.1: Compliance Score Improvement Chart] xychart-beta title "Compliance Score Improvement x-axis [TechStart', 'ShopEasy", "HealthTrack", "CloudDocs , "GameZone", EduLearn", "FoodieApp", "SecureBank" "SmartHome", "TravelBuddy' (%) 0100 y-axis xis 'Compliance Score bar [45, 52, 39, 61, 56, 43, 49, 71, 63, 58] bar [87, 90, 85, 92, 89, 86, 90, 96, 92, 90]

5.1.3 Processing Time Analysis

TABLE 5.2: Processing Time by Phase

Phase

Average Time

Notes

Phase 1: Parsing

0.5 seconds

Format-dependent; PDF parsing takes longer

Phase 2: Compliance Check

2.3 seconds

Rule complexity and document length affect time

Phase 3: AI Generation

3-5 minutes

Depends on number and severity of violations

Total Average

4-6 minutes

Per document

Phase 3 (AI Generation) dominates the processing time because each violation requires RAG retrieval, prompt construction, LLM generation, and review agent validation. The use of Llama 3.1 running locally via Ollama introduces infer- ence latency per generation call, but this trade-off is acceptable given the privacy benefits of local deployment.

5.1.4 RAG Effectiveness

The impact of RAG integration was measured by comparing system output with and without access to the RAG knowledge base:

TABLE 5.3: RAG Effectiveness Comparison

Metric

Without RAG

With RAG

Improvement

Content Relevance

67%

89%

+22%

Legal Accuracy

71%

92%

+21%

Style Consistency

58%

94%

+36%

Hallucination Rate

15%

3%

-12%

The most significant improvement from RAG integration is in Style Consistency (+36%), which demonstrates the critical importance of grounding generation in real-world examples. Without RAG, the LLM produces generic, conversational text that does not match the formal, precise register expected of privacy policies. With RAG, the retrieved examples serve as implicit style guides, teaching the model the appropriate vocabulary, sentence structure, and legal tone for privacy policy documents.

The reduction in hallucination rate from 15% to 3% is particularly significant in the compliance domain, where generating false or misleading policy statements could expose organisations to legal liability. The RAG-retrieved examples con- strain the model's generation space, making it substantially less likely to fabricate non-existent legal provisions or describe data practices that are not grounded in real privacy policies.

Legal Accuracy (+21%) improved because the RAG examples provide the model with correct legal terminology, standard clause structures, and appropriate regulatory references. Content Relevance $(+22\%)$ improved because category- scoped retrieval ensures that the examples provided to the LLM are directly rele- vant to the violation being addressed.

5.2 Novelty and Contributions

This section highlights the original contributions of the Compliance Automation System and positions them within the broader landscape of privacy policy analysis tools. The system introduces several innovations that distinguish it from existing template-based generators and standalone LLM approaches.

5.2.1 Key Innovations

[Image: FIGURE 5.2: Project Innovation Areas] Parse Check End-to-End Generate No API Customizable costs Privacy-focused Local LLM Enhance parts Add missing Project Novelty Augmentation 801 real examples RAG Integration Grounded generation Reduced hallucination Multi-Agent Reviewer Agent Analyst Agent Generator Agent Preserve original

5.2.2 Contribution Summary

The following enumerated list details the ten major contributions delivered by the system, spanning technical architecture, AI methodology, and user-facing features:

First RAG-enhanced privacy policy generation system: Combines retrieval from real policies with LLM generation for grounded, accurate con- tent.

Multi-agent collaborative architecture: Specialised agents (Analyst, Generator, Reviewer) work together for higher-quality output through sep- aration of concerns.

OPP-115 standard integration: Comprehensive implementation of all 10 privacy practice categories with severity-based violation detection.

Content augmentation vs. replacement: Preserves compliant origi- nal content while adding/improving non-compliant sections, honouring the organisation's authentic voice.

Privacy-first local deployment: Uses Ollama for on-premise LLM infer- ence, ensuring document data never leaves the organisation.

Batch processing capability: Process entire OPP-115 dataset (115 doc- uments) with progress tracking.

Custom compliance rules engine: User-definable rules with keyword matching, severity levels, and OPP-115 category alignment.

Multi-format export system: Improved documents exportable as PDF (ReportLab), styled HTML, and plain text.

Real-time analytics dashboard: Interactive Chart.js visualisations in- cluding compliance score trends, processing status distribution, and compli- ance distribution.

Document comparison with sync scrolling: Side-by-side original vs. improved view with AI-generated section highlighting and synchronised scroll behaviour.

5.2.3 Comparison with Existing Solutions

Table 5.4 provides a feature-by-feature comparison between three categories of existing solutions template-based generators (e.g., Termly, iubenda), standalone LLM approaches (e.g., ChatGPT-based drafting), and our integrated system. The comparison demonstrates that our system is the only solution offering compliance checking. RAG grounding, multi-agent architecture, and batch processing in a single platform.

TABLE 5.4: Feature Comparison with Existing Solutions

Feature

Template Generators

LLM-Only

Our System

Customisation

Low

High

High

Legal Accuracy

Medium

Low

High

Compliance Checking

No

No

Yes

RAG Grounding

No

No

Yes

Multi-Agent

No

No

Yes

Local Deployment

Yes

Rare

Yes

Batch Processing

No

No

Yes

Custom Rules

No

No

Yes

Multi-Format Export

Limited

No

Yes

Analytics board

No

No

Yes

Document Comparison

No

No

Yes

5.3 Future Enhancements

While the current system delivers a fully functional compliance automation pipeline,
several enhancements are planned across three time horizons. These improvements
would expand regulatory coverage, improve generation quality, and add enterprise-
ready features for production deployment.

5.3.1 Short-term (3-6 months)

The short-term roadmap focuses on improving the real-time user experience and
broadening regulatory coverage beyond the OPP-115 standard:

WebSocket Real-time Updates

• Replace HTTP polling with WebSocket connections

Instant status updates during processing

Multi-regulation Support

Add GDPR-specific compliance rules

• Add CCPA-specific compliance rules

• Regulation selection in UI

Document Version Control

Track document revisions

Diff view between versions

5.3.2 Medium-term (6-12 months)

Medium-term enhancements focus on improving generation quality through model
fine-tuning and adding enterprise features such as authentication and multi-language
support:

Fine-tuned LLM

• Train model specifically on privacy policy corpus

• Improved domain-specific generation quality

Compliance Prediction

ML model to predict post-improvement compliance score

• Optimisation for target compliance levels

Multi-language Support

• Process non-English privacy policies

• Generate content in multiple languages

API Authentication

JWT-based authentication

Role-based access control (RBAC)

5.3.3 Long-term (12+ months)

Long-term goals aim to transform the system from a standalone tool into a con-
tinuous compliance monitoring platform with collaborative features:

Continuous Monitoring

Web scraping for policy change detection

Automated re-analysis on updates

Legal Team Collaboration

Annotation and commenting system

• Approval workflows with notifications

Regulatory Update Integration

• Automatic rule updates when regulations change

• Al-powered regulatory change detection

Industry Templates

• Healthcare (HIPAA)

Finance (GLBA)

Children's apps (COPPA)

5.3.4 Research Extensions

Beyond product features, several research directions would further advance the
academic contributions of this work:

Explainable AI Integration

• Attribution of generated content to source examples

Confidence scores for each generated section

Adversarial Testing

Test against maliciously crafted policies

• Robustness evaluation

Database Migration

• Migrate persistent storage from JSON files to SQLite or PostgreSQL
Enable full-text search across processed documents

5.4 Conclusion

This project successfully demonstrates an AI-powered Compliance Automa-
tion System that addresses the critical need for efficient privacy policy analysis
and improvement. The system represents a significant advance in the field of Legal
Technology (LegalTech) by bridging the gap between privacy policy analysis and
automated content generation a capability that has not been previously achieved
in an integrated manner. The three-phase pipeline Document Parsing, Compli-
ance Checking, and RAG-Enhanced AI Generation provides a comprehensive,
end-to-end solution for organisations struggling with privacy policy compliance.

Unlike template-based generators that produce generic content or standalone LLMs
that may hallucinate, our system leverages a carefully constructed RAG knowl-
edge base of 801 real privacy policy sections to ensure that generated content is
grounded in real-world conventions and employs legally appropriate language.

5.4.1 Theoretical Contributions

This project makes several theoretical contributions to the domains of NLP, AI,
and Legal Technology:

RAG for Regulatory Compliance: We demonstrate that Retrieval-Augmented
Generation is exceptionally well-suited for regulatory compliance applica-
tions, where factual precision and domain-specific terminology are essential.
The 36% average improvement in compliance scores validates that grounding
LLM generation in domain-specific examples is substantially more effective
than relying on parametric knowledge alone.

Multi-Agent Quality Assurance: The three-agent architecture (Analyst
→ Generator → Reviewer) provides a novel framework for quality assurance
in legal text generation. The separation of concerns between analysis, gener-
ation, and review mirrors professional legal drafting workflows and produces
higher-quality output than single-pass generation.

Content Augmentation over Replacement: Our system introduces the
principle of augmentation over replacement preserving compliant original
content while adding or improving non-compliant sections. This approach
honours the organisation's authentic voice and unique data practices while
ensuring comprehensive coverage.

Privacy-Preserving AI: By deploying LLMs locally through Ollama, we
demonstrate that privacy-sensitive AI applications can achieve strong per-
formance without reliance on cloud-based APIs, resolving a fundamental
tension between Al capability and data privacy.

5.4.2 Practical Achievements

Beyond the theoretical contributions, the system delivers a production-ready tool
with a comprehensive set of features:

Key Features Delivered:

Multi-format document parsing (TXT, HTML, PDF, DOCX)

• Compliance checking against 10 OPP-115 categories

RAG-enhanced content generation with 801 real examples

• Multi-agent architecture for quality generation

• Average compliance improvement of 36%

Full-featured web interface with 7 dedicated pages

Multi-format export (PDF, HTML, plain text)

Batch file upload and sequential processing

Full OPP-115 dataset processing (115 policies) with live progress

Custom compliance rules engine with CRUD interface

Real-time analytics dashboard with Chart.js trend visualisation

• Side-by-side document comparison with synchronised scrolling
• Processing ETA estimation and activity logging

Data persistence across server restarts (JSON-based storage)

• Auto-refreshing dashboard with toast notification system

. Document deletion with full cleanup of related files

• Docker-ready for deployment with NGINX configuration

Markdown-to-HTML documentation converter with Mermaid support

5.4.3 Broader Impact

The system has significant implications for multiple stakeholder groups:

• Small and Medium Enterprises: Democratises access to compliance tools
that were previously available only through costly legal consultations, mak-
ing privacy compliance more accessible.

• Legal Professionals: Accelerates the policy drafting process by provid-
ing legal teams with a strong first draft grounded in real-world examples,
allowing them to focus on customisation and review.

• Regulatory Bodies: Demonstrates how AI can assist in compliance mon-
itoring, potentially enabling oversight of the millions of organisations that
currently lack adequate privacy policies.

• Privacy Research Community: Provides a functional implementation
framework for RAG and multi-agent architectures in the legal domain, of-
fering open-source tools and methodologies for subsequent research.

The system demonstrates that combining traditional rule-based compliance check-
ing with modern RAG-enhanced LLMs can produce legally accurate, contex-
tually appropriate, and stylistically consistent privacy policy content. The
local LLM deployment ensures data privacy, while the multi-agent architecture
ensures generation quality through structured agent collaboration.

This work contributes to the growing field of Legal Technology (LegalTech)
and demonstrates that advanced NLP techniques, when properly grounded through
retrieval augmentation and quality-assured through multi-agent workflows, can
provide practical, reliable solutions for regulatory compliance automation.

Bibliography

[1] Wilson, S., et al. (2016). "The Creation and Analysis of a Website Privacy
Policy Corpus." Proceedings of the 54th Annual Meeting of the Association for
Computational Linguistics (ACL).

[2] Harkous, H., et al. (2018). "Polisis: Automated Analysis and Presentation of
Privacy Policies Using Deep Learning." 27th USENIX Security Symposium.

[3] Lewis, P., et al. (2020). "Retrieval-Augmented Generation for Knowledge-
Intensive NLP Tasks." Advances in Neural Information Processing Systems
(NeurIPS).

[4] Touvron, H., et al. (2023). "Llama 2: Open Foundation and Fine-Tuned Chat
Models." Meta AI Research.

[5] Reimers, N., & Gurevych, I. (2019). "Sentence-BERT: Sentence Embeddings
using Siamese BERT-Networks." Proceedings of the 2019 Conference on Em-
pirical Methods in Natural Language Processing (EMNLP).

[6] OPP-115 Dataset. Usable Privacy Policy Project. https://usableprivacy.
org/data

[7] GDPR. "General Data Protection Regulation (Regulation (EU) 2016/679)."
Official Journal of the European Union, 2016.

[8] CCPA. "California Consumer Privacy Act of 2018." Title 1.81.5 of the Cali-
fornia Civil Code, 2018.

[9] Vaswani, A., et al. (2017). "Attention Is All You Need." Advances in Neural
Information Processing Systems (NeurIPS).

[10] Sadeh, N., et al. (2013). "The Usable Privacy Policy Project." Technical Re-
port, Carnegie Mellon University.

[11] Andow, B., et al. (2020). "PolicyLint: Investigating Internal Privacy Policy
Contradictions on Google Play." 29th USENIX Security Symposium.

[12] Zaeem, R.N., & Barber, K.S. (2019). "A Large Publicly Available Corpus
of Website Privacy Policies Based on DMOZ." Proceedings of the 11th ACM
Workshop on Artificial Intelligence and Security.

[13] McDonald, A.M., & Cranor, L.F. (2008). "The Cost of Reading Privacy Poli-
cies." $I/S$: A Journal of Law and Policy for the Information Society, 4(3),
543-568.

[14] Obar, J.A., & Oeldorf-Hirsch, A. (2020). "The Biggest Lie on the Internet: Ig-
noring the Privacy Policies and Terms of Service Policies of Social Networking
Services." Information, Communication & Society, 23(1), 128-147.

[15] Reidenberg, J.R., et al. (2015). "Ambiguity in Privacy Policies and the Impact
of Regulation." The Journal of Legal Studies, 45(S2), S163-S190.

[16] Hevner, A.R., et al. (2004). "Design Science in Information Systems Re-
search." MIS Quarterly, 28(1), 75-105.

[17] Wooldridge, M., & Jennings, N.R. (1995). "Intelligent Agents: Theory and
Practice." The Knowledge Engineering Review, 10(2), 115-152.

[18] Wu, Q., et al. (2023). "AutoGen: Making Next-Gen LLM Apps Possible
through Multi-Agent Conversation." arXiv preprint arXiv:2308.08155.

[19] Srinath, $M.,$ et al. (2021). "PrivaSeer: A Privacy Policy Search Engine." Pro-
ceedings of the Web Conference 2021.

[20] Devlin, $J.,$ et al. (2019). "BERT: Pre-training of Deep Bidirectional Trans-
formers for Language Understanding." Proceedings of NAACL-HLT 2019.