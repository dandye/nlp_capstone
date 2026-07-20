TLP:CLEAR 
This document is marked TLP:CLEAR. Disclosure is not limited. Sources may use TLP:CLEAR when information carries 
minimal or no foreseeable risk of misuse, in accordance with applicable rules and procedures for public release. 
Subject to standard copyright rules, TLP:CLEAR information may be distributed without restriction. For more information 
on the Traffic Light Protocol, see Traffic Light Protocol (TLP) Definitions and Usage. 
TLP:CLEAR
 
 
Barriers to Secure OT Communication: 
Why Johnny Can’t Authenticate
Publication: February 10, 2026
Cybersecurity and Infrastructure Security Agency

---

Barriers to Secure OT Communication: Why Johnny Can’t Authenticate TLP:CLEAR
Guidance at a Glance
Title Barriers to Secure OT Communication: Why Johnny Can’t Authenticate 
Original Publication February 10, 2026 
Executive Summary 
Many critical infrastructure organizations maintain legacy industrial protocols—
which are older communication standards key. Malicious actors with access to the 
OT network can exploit the legacy protocols’ lack of: 
 Strong safeguards that prevent data from being altered (integrity), 
 Methods to confirm the identity of the device sending the message 
(authentication), and 
 Means of protecting sensitive data. 
To drive down this risk of exploitation, in which a malicious actor could 
impersonate a device or modify a message, CISA and partners: 
1. Conducted voice of customer (VoC) research to better understand the 
barriers keeping owners and operators from adopting existing secure 
communication protocols. 
2. Analyzed the VoC findings to provide a clearer path for (a) critical 
infrastructure organizations to adopt secure communication protocols and
(b) manufacturers to reduce the cost and complexity of adopting secure 
communication protocols in their products.
This guidance provides recommendations based on the VoC analysis to both 
critical infrastructure organizations and to manufacturers.
Key Actions 
Critical infrastructure owners and operators: Implement the list of 
recommendations in Appendix A to remove barriers to adopting secure 
communication protocols.
Manufacturers: Implement the list of recommendations in Appendix A to 
improve customer usability of secure communication protocols in your 
products.
Intended Audience 
Organizations: Critical infrastructure organizations and OT manufacturers 
Sectors: Though this guidance is applicable to all critical infrastructure sectors, 
the research for this guidance focused on owners, operators, and manufacturers
in the following sectors: Water and Wastewater Systems, Transportation Systems, 
Chemical, Energy, and Food and Agriculture. 
Roles: Defensive cybersecurity analysts and security systems managers 

---

Table of Contents 
Guidance at a Glance ................................................................................................................................................... 2
Executive Summary ..................................................................................................................................................... 4
Introduction ................................................................................................................................................................... 5
Encryption and Signing in OT ...................................................................................................................................... 7
Motivating Factors for Pursuing Secure Communication ...................................................................................... 7
Barriers to Adopting Secure Communication .......................................................................................................... 8
Costs Delay Adoption ......................................................................................................................................... 8
Procurement................................................................................................................................................... 8
Deployment and Maintenance...................................................................................................................... 9
Cost Recommendations for Manufacturers...............................................................................................10
Availability Concerns Delay Security Adoption................................................................................................10
Observability .................................................................................................................................................11
Latency and Bandwidth...............................................................................................................................11
Confidence....................................................................................................................................................11
Availability Recommendations for Manufacturers ....................................................................................12
PKI Difficulties Dissuade Operators................................................................................................................12
Complexity During Deployment and Provisioning ......................................................................................12
Complexity During Operations.....................................................................................................................13
Connectivity Risks ........................................................................................................................................13
PKI Usability Recommendations for Manufacturers .................................................................................13
Removing Barriers to Secure Communication ..................................................................................................... 14
Ending Proprietary Limitations ........................................................................................................................14
Modular Software and Hardware ....................................................................................................................14
Available Testing Environments ......................................................................................................................14
Considerations for Post-Quantum Cryptography .................................................................................................. 14
Opportunity for Action ............................................................................................................................................... 15
Conclusion .................................................................................................................................................................. 15
Acknowledgements ................................................................................................................................................... 15
Appendix A. Summary of Recommendations ....................................................................................................... 16
Recommendations for Owners and Operators...............................................................................................16
Recommendations for Manufacturers............................................................................................................17

---

Executive Summary
Legacy industrial protocols lack the basic authentication and integrity checks necessary to prevent a threat 
actor from impersonating a device or modifying a message in transit. Despite this security weakness, the 
control systems community has not widely adopted the secure versions of these protocols that enable 
secure communication. CISA conducted customer research within the community to understand barriers to 
secure communication, interviewing operational technology (OT) asset owners and operators, in their 
individual capacities, across the following critical infrastructure sectors: Water and Wastewater Systems, 
Transportation Systems, Chemical, Energy, and Food and Agriculture. 
Through the interviews, CISA found that OT asset owners have a clear desire for the integrity and 
authentication benefits secure communication can provide. Despite this, those same asset owners 
expressed that the solutions are complex and costly to maintain, especially compared to other forms of 
security. In this guidance, CISA provides owners and operators with aggregated lessons learned for safely 
implementing secure communication. This guidance also provides OT manufacturers with 
recommendations for reducing the identified cost and complexity issues preventing secure communication 
in OT. A summary of these recommendations is listed in Appendix A. 
Parts of OT networks will inevitably use legacy protocols until organizations replace them with newer 
components. However, operators will only use the secure protocol in new components if the technology is 
usable by operators in an OT environment. Secure communication in OT is a long-term effort, requiring 
collaboration between asset owners and operators, system integrators, service providers, and OT 
manufacturers. Asset owners and integrators should use this guidance to avoid disruptions from secure 
communication and identify what to prioritize when procuring new components. OT manufacturers should 
use the lessons from this customer research to reduce customer friction with security and ultimately create 
a more usable, safe product. 

---

Introduction
OT networks that support critical infrastructure primarily rely on legacy industrial protocols originally 
designed for reliability rather than cybersecurity. As a result, these networks lack: 
• Robust integrity protections, 
• Mechanisms for authenticating the component that is communicating, and 
• Means of protecting sensitive data. 
Secure versions of industrial protocols have existed since the early 2000s (e.g., Distributed Network 
Protocol 3 [DNP3] to DNP3 Secure Authentication version 5 [DNP3-SAv5], Common Industrial Protocol [CIP] 
to CIP Security, Modbus to Modbus Security, Open Platform Communications Data Access [OPC DA] to OPC 
Unified Architecture [UA]). However, many OT systems built in 2026 still rely on protocol implementations 
designed decades ago, leaving their networks fully trusting anyone with access. Specifically, legacy 
industrial protocols do not protect against engineering mistakes, integrity errors, much less threat actors 
targeting OT environments.2
1
The existence of secure versions of the protocols begs the question: Why are organizations not 
implementing them? The cybersecurity community has asked versions of this question before, most 
famously in the seminal 1999 paper Why Johnny Can’t Encrypt and its many follow-ons, which 
demonstrate that a technical solution’s maturity is irrelevant if the target audience cannot use the solution. 
“Johnny” often has the technical tools to be secure but cannot practically use them due to the hurdles of 
cost and complexity. This guidance aims to address this issue and examines why asset owners and 
operators (Johnny) cannot authenticate and guarantee the integrity of OT data in transit.
3
To understand how to help the OT community shift away from legacy industrial protocols to more secure 
technology, CISA and partners—including OT manufacturers and protocol standard development 
organizations—conducted voice of customer (VoC) research focused on asset owners and operators of 
varying maturity across the Water and Wastewater Systems, Transportation Systems, Chemical, Energy, 
and Food and Agriculture Sectors. The research used individual and group interviews to identify how asset 
owners understand secure communication in OT, and what barriers organizations encounter on the user 
journey across procurement, design, deployment, and operations. Note: Organizations take different 
approaches to splitting responsibility between information technology (IT), engineering and operations, and 
OT security teams; this is reflected in their responses. 
1 Note: In this guidance, the term “secure protocols” refers to the security capabilities of the protocol, not the security 
of the protocol implementation.
2 “PRC State-Sponsored Actors Compromise and Maintain Persistent Access to U.S. Critical Infrastructure,” 
https://www.cisa.gov/news-events/cybersecurity-advisories/aa24-038a. 
3 Alma Whitten and J. D. Tygar, “Why Johnny Can’t Encrypt: A Usability Evaluation of PGP 5.0,” in Proceedings of the 
8th USENIX Security Symposium (Washington, DC: USENIX Association, 1999), 169–184. 
https://www.usenix.org/conference/8th-usenix-security-symposium/why-johnny-cant-encrypt-usability-evaluation-pgp￾50. 

---

This guidance intends to produce a clearer path for:
• Owners and operators who wish to safely implement secure communications, and
• OT manufacturers, such as industrial automation and control system vendors, suppliers, and 
original equipment manufacturers, who wish to improve the usability of secure communications by 
removing the barriers facing their customers.
This guidance expands on the secure communication concepts raised in previous Secure by Design OT 
publications. For more background on CISA’s Secure by Design initiative for OT, read the joint guidance 
Secure by Demand: Priority Considerations for Operational Technology Owners and Operators when 
Selecting Digital Products.
See Figure 1 for a summarized journey map demonstrating operator’s goals and negative experiences 
while adopting secure communication, in addition to suggestions for how manufacturers can address any 
challenges.
Figure 1: Secure Communications Operator Journey Map4
4 OPEX stands for operational expenditure. 

---

Encryption and Signing in OT
Before analyzing the interviews, it is important to understand the nuance of signing and encryption within 
the bucket of secure communication. Research interviews highlighted that operators carry different 
assumptions when discussing if secure communication must include encryption, and what is or is not 
encrypted.
This guidance defines signing as adding integrity and authentication, and it defines encryption as adding 
confidentiality. Signing and encrypting are separate but related security capabilities that apply identity and 
access management to communication. Operators should prioritize the integrity and authentication 
protections of signing. Signing can take place without encryption. Encrypting typically includes signing by 
default, but operators need to verify their systems are checking the integrity and authenticity of a message.
A common point of confusion was distinguishing between encryption of operations and encryption of 
network management. As discussed further in this guidance:
 Encryption of operations, such as engineering and process control data, can result in safety 
impacts from a lack of inspection (limiting view) or increased latency. 
 Encryption of network management, such as changing passwords or updating keys, is necessary to 
protect those secrets from disclosure or tampering. 
This guidance highlights VoC-driven use cases for signing without encryption, signing all traffic and 
encrypting some traffic, and signing and encrypting all traffic. After reviewing this guidance, operators 
should be able to articulate the trade-offs of signing and encryption rather than treating them as a blanket, 
operationally burdensome practice. 
Motivating Factors for Pursuing Secure Communication
Our research found that the core motivation for adopting secure communications is that asset owners want 
to protect the integrity and authenticity of the data flowing through their OT systems. Message signing is 
the standard way of adding this protection. Signing messages allows an operator to achieve tamper 
resistance and verify that components are who they say they are (i.e., integrity and authentication). 
Operators cited actor-in-the-middle attacks, unauthenticated commands, configuration changes, and 
firmware updates as specific motivating threats. Notably past OT incidents, such as Industroyer, could have
been detected and prevented through authenticated OT communication.
The other motivating capabilities involved protecting the secrecy of data through encryption. Most 
operators focused on three main use cases for encryption: 
 Pushing updates into the field.
 Aggregating data from the field.
 Preventing inspection if a threat actor establishes a foothold. 

---

An example of pushing updates is securely updating all passwords in the field without visiting each site. 
Organizations should require data encryption for password protection. Data aggregation secures 
communication from a field edge to a security operations center (SOC), enterprise historian, or supervisory 
control and data acquisition (SCADA) server. Organizations then use the collected data for tracking 
operations or monitoring security incidents. Notably, these use cases do not impose large bandwidth 
requirements on the field network. 
Inspection prevention use cases vary. One interviewed organization pre-emptively encrypts new, higher 
exposure, wireless connections used for telemetry, which engineers commonly used for other purposes, 
including sending sensitive information. Another interviewed organization encrypts operational data to 
prevent a threat actor from understanding the engineering enough to produce a sustained system impact.
Barriers to Adopting Secure Communication
Through the VoC research, CISA found that, in their pursuit of secure communications, operators 
encountered barriers from initial conception and procurement, through deployment and operations. The 
two main barriers were cost and the availability concerns stemming from encrypting data. This section 
examines the source of secure communication costs throughout a system’s lifecycle and how the location 
of secure communication changed perceptions around availability concerns. Additionally, we examine the 
role of public key infrastructure (PKI) and how operators currently interface with it. 
Costs Delay Adoption
Several interviewed organizations considered deploying secure communications before deciding against it 
due to initial and ongoing costs, which included:
 Retrofitting legacy infrastructure. 
 Upgrading hardware to support cryptographic operations. 
 Integrating certificate management practices or licensing fees. 
 Training personnel. 
 More complex field operations. 
 Maintaining compliance with evolving standards. 
These costs manifested in different ways throughout the product lifecycle, from procurement through 
deployment and maintenance.
Procurement
The first choice for organizations was whether to upgrade their existing components or to wrap traffic. 
Upgrading means replacing the component or communications card. Alternatively, wrapping has the 
component continue using the insecure protocol, but now with a gateway to wrap each insecure packet in 
security. 

---

Operators cited that the procurement cost of upgrading their component to secure communications is
often as much as the cost of the original component. Additionally, OT vendors may charge a licensing fee to 
enable a secure communications server. When faced with these costs, many asset owners chose
segmentation and continuous monitoring controls—which they perceive as having sufficiently comparable 
benefits and more predictable costs—over secure communications.
Alternatively, operators that chose to instead wrap their traffic faced a smaller procurement cost but 
received a less comprehensive solution. Wrapping involves implementors placing a gateway in front of key 
components, or groupings of components, that authenticate communication in or out of that segment. 
Although a gateway provides significant improvements to an unauthenticated network, it does not protect 
against the risk of compromise beyond the node it is in front of. Operators often pair traffic wrapping with 
component upgrades so new components do not revert to insecure legacy protocols. Operators can more 
easily justify the cost of securing north-south traffic than east-west traffic because edge devices typically 
enforce segmentation while securing communications leaving the field network. By contrast, east-west 
controls limit lateral movement within the field network. It is logical to prioritize preventing unauthorized 
access to the field network, though east-west traffic must eventually be considered as threat actors have 
routinely shown they can access field networks.
Organizations also used wrapping when they supported multiple vendors or did not trust existing vendor 
secure protocol implementations. Operators wrapped legacy OT communication in transport layer security, 
to avoid vendor implementations and the potential interoperability challenges. More consequentially, one 
asset owner incurred the cost of removing architecture after buying a proprietary secure communications 
solution from a vendor that subsequently went out of business. Many OT communication protocols support 
formal certification programs that verify products from different vendors can work together reliably. In 
cases where certification is unavailable, vendors often participate in interoperability testing events,
sometimes called “plug-fests,” which demonstrate compatibility. Operators should ensure that vendors get
open standard protocol implementations certified, including security aspects. 
When faced with these overall procurement costs, several operators expressed a lack of confidence in the 
long-term stability of secure communication. They cited that the protocol, or key length required by a given 
protocol, may change at any time and make their investment moot. Operators should search for products 
that support crypto-agility, the ability to assure that the product’s operational lifespan is not limited by the 
lifespan of any single algorithm. A system owner can identify a crypto-agile component by verifying whether 
it supports configurable or upgradable cryptographic algorithms through firmware updates, support of 
multiple cipher suites, or integration with external key management systems. Non-crypto-agile components 
typically rely on fixed, hardcoded algorithms that require hardware replacement to change.
Deployment and Maintenance
Operators that decided to procure a system or component considered the cost of deploying and 
maintaining a secure communications infrastructure. Several operators cited the complexity and overhead 
associated with deploying and managing a secure communication infrastructure. They described the need 
to hire a third-party service provider for assistance with deployment of a public key infrastructure (PKI) and
to retain those services to ensure that nothing breaks. 

---

The overhead costs generated by this perceived complexity prevented them from using secure 
communications. See the end of the PKI Difficulties Dissuade Operators section for more on the issue of 
PKI complexity. Operators should seek out vendor solutions that simplify secure workflows (e.g., 
management tools, wizards, system integrator support). 
The interviewees often phrased these cost issues in terms of trade-offs. Operators weighed the cost of secure 
communications against strengthening segmentation, buying a continuous monitoring solution, paying down 
other tech debt (e.g., end-of-life Windows systems), and cybersecurity education. They found it easier and less 
costly to segment or add security components to their system rather than to use secure communication 
software often already in their components. From a technical perspective, secure communication enables 
micro-segmentation and simplifies continuous monitoring by removing categories of spoofing and integrity 
attacks. Operators deploying secure communication should strategically apply it to remote access paths, 
communication between functional or network boundaries, and firmware uploads and logic changes to limit 
access to the OT network and mitigate the impact of threat actors on the OT network.
Cost Recommendations for Manufacturers 
Manufacturers can address cost barriers through the following practices:
 Build systems with crypto-agility to remove the fear of buying at the wrong time.
 Be transparent about security infrastructure costs.
 Include secure communication capabilities by default.
 Drive out complexity to reduce costs and track key performance indicators (KPIs) associated with 
the usability of security features. 
o For example, set-up time or whether security features are disabled.
 Maximize opportunities to transition from legacy communication patterns.
○ Default to the secure option.
○ Guide the user for the required security infrastructure, such as PKI.
○ For integrated systems, pre-configure the system to use secure communications as a form of 
micro-segmentation.
Availability Concerns Delay Security Adoption
A core requirement of any security feature is that it does not disrupt normal operations, engineering, or 
business processes. Many operators feared that layering security on top of communications would disrupt 
operations. Prior poor experiences from adopting security solutions had a long-term, negative effect on an 
operator’s interest in trying a new security solution. The fears regarding disruption caused by secure 
communications can be sorted into three categories: observability, latency and bandwidth, and confidence.

---

Observability
The interviewees generally assumed that secure communication means that all traffic is encrypted, which 
could complicate inspection for debugging and security monitoring. Larger operators saw fewer issues with 
encryption but mostly focused on north-bound traffic from the field. One way to address encryption’s 
availability problem is by only encrypting sensitive communication (e.g., passwords, key exchanges, logic 
updates) and signing the rest to add integrity and authentication without limiting observability. Encryption 
does not necessarily limit observability depending on how operators configure historians and monitoring 
solutions. 
Latency and Bandwidth
Operators with older infrastructure hypothesized there would be computational challenges. In essence,
these operators assumed that the underlying network infrastructure cannot support the increased 
bandwidth and/or the components lack the computational resources or efficiency. For example, IEC 
61850 mandates that a Type 1A protection message has a maximum allowable end-to-end delay of 3 
milliseconds. There is an unacceptable delay if the CPU cycles for signing and verifying the signature are 
too slow. Newer components, which have better compute resources and cryptographic libraries custom 
designed for embedded systems, can mitigate these very real latency concerns. 
5
On the network side, the bandwidth of the links in and between OT sites can be a challenge if encryption 
adds a substantial number of bits over the wire. Bandwidth constraints require infrastructure upgrades. 
CISA strongly encourages organizations test whether upgrades are necessary and if the physical network 
bandwidth or the component’s software is the bottleneck. Regardless of these latency and bandwidth 
constraints, if organizations do not authenticate protection messages, threat actors can exploit them. 
Confidence
Interviewees disagreed on whether secure communications would disrupt operations. A person’s opinion
largely aligned with where they sit in their organization between engineering and operations and acting as 
a general security practitioner. Their different risk tolerances lead to organizations applying secure 
communications to different components, in different locations, and with different automated responses to 
certificate issues.
For the location of secure communication, security practitioners would often focus on north-bound traffic 
as it reduced dependencies on field communications. This placement typically aligned with the security 
practitioner’s area of authority ending near the supervisory layer of the OT network and with it being more 
difficult for them to modify field devices. Operators with access to field devices were more risk averse than 
security practitioners when applying secure communication to a brownfield deployment with legacy 
components, due to a lack of confidence in the technology being non-disruptive. 
5 This is an international standard for power utility automation maintained by the International Electrotechnical 
Commission, https://webstore.iec.ch/en/publication/6028. 

---

A key question from operators is how they should handle components with expired or invalid certificates. 
The concern is that a safety critical packet, such as a protection command, could be erroneously dropped
the source component’s certificate expired. One approach is to not check if certificates are expired, 
effectively only dropping packets with certificates that were never valid. This forces a stealthy threat actor 
to compromise the component sending the protection command without breaking normal operations if a 
certificate expires. Allowing certificates to effectively never expire is not a best practice but can be an 
intermediary solution while operators test key management infrastructure and gives operators the 
assurance that an expired certificated on a component will not impact critical operations.
Operators sensitive to secure communications disrupting brownfield operations should begin with sign-only 
and packet dropping disabled, then dropping unauthenticated packets as confidence in the infrastructure 
increases. Note that logging of certificate issues is detection oriented while dropping messages is 
prevention oriented. Hacktivists or threat actors whose goals are creating societal panic are unlikely to be 
concerned with stealth when executing their final attack. CISA strongly recommends organizations 
transition from logging to dropping packets as confidence increases and their secure communications 
solutions increasingly adopt the recommendations included in this guidance.
Availability Recommendations for Manufacturers
Manufacturers can address availability barriers through the following practices:
 Use open standards and interoperability testing and certification (wherever possible), which should
increase confidence that the secure communications solution will not disrupt operations.
○ Note: Operators tended to blame the secure protocol first, not the vendor, when facing 
interoperability challenges, which has a broad dampening effect on security. 
 Publish testing results to demonstrate minimum required network bandwidth for secure 
communications when paired with the resources of common products.
 Provide clear upgrade paths for legacy infrastructure.
PKI Difficulties Dissuade Operators
Almost every operator interviewed mentioned challenges with deploying and maintaining PKI. Beyond the 
themes already discussed, PKI often resulted in conversations about complexity, during deployment and 
operations, and connectivity risks. Notably there are alternate solutions to PKI, such as pre-shared keys, 
which interviewees did not mention in interviews. This focus on PKI may be indicative of interviewees not 
being aware of alternative solutions and a need for better communication from manufacturers. 
Complexity During Deployment and Provisioning
Initial key provisioning requires that operators configure a certificate manager, create certificates, and 
deploy them to each component. Many operators expressed that they needed support from a system 
integrator or managed service provider for these activities. The level of support varies based on the OT 
protocol, with newer versions of protocols (e.g., DNP SAv2, DNP SAv5, DNP3-SL) favoring increasing 
automation that lessens the complexity for the end user. 

---

Operators should seek products that simplify the initial key provisioning, as well as system integrators that 
have experience setting up PKI for the selected OT protocol. Long-term, operators should seek secure 
discovery and provisioning capabilities that allow a certificate manager to quickly onboard new 
components. 
Complexity During Operations
Field-level secure communication can operate in a responsibility gray-zone, with field components 
(programmable logic controllers, remote terminal units, sensors, actuators, etc.) being the responsibility of 
operators, and the higher-level network infrastructure and PKI being the responsibility of the security 
teams. This can leave operators who have no experience managing PKI in charge of key deployment and 
rotation. 
Operators found success using commercial or no-cost software that supports secure OT and general 
management protocols that automate their key management, prioritizing systems that are difficult to 
access and important to operations. Using management software also allowed for more fine-grained 
segmentation, with functional groupings of OT systems authenticated for communication with each other 
rather than treating OT as a flat network. 
Connectivity Risks 
One operator perceived PKI as requiring them to break segmentation, under the assumption that the 
certificate authority must be in a central site which then forces bi-directional communication from the field. 
Operators should balance ease of management for their system of systems with this connectivity risk. In 
theory, every field site could use its own certificate manager or use push-based architectures where the 
client initiates all key updates, trading increased complexity for reduced connectivity.
PKI Usability Recommendations for Manufacturers
Manufacturers can address PKI usability issues through the following practices:
 Develop integrator-facing deployment guidance that enables secure communication by default. 
Manufacturers can reduce deployment costs by minimizing the configuration gap between legacy 
(brownfield) systems and new (greenfield) secure installations (e.g., standardizing interfaces, 
providing pre-configured templates, and offering integration support for common OT environments). 
 Follow Secure by Default best practices. 
 Ensure products have a clear design preference for secure deployment and operations. Guide the 
customer to that safe and secure state and away from risky operating models. Examples of risky 
operating models relating to secure communications include:
○ Connecting OT and IT to a central identity and access management system.
○ Creating inflexible IT dependencies for a critical engineering process.
○ Restricting inspection of operational data.

---

Removing Barriers to Secure Communication
Asset owners identified solutions that would lower their barriers for secure protocol adoption. 
Ending Proprietary Limitations 
Almost every asset owner referenced proprietary protocols and software as an impediment to securing 
their system. Some operators cited interoperability issues that locked them into a particular vendor and 
limited their ability to inspect traffic. The proposed solution typically involved following open standards and 
conformance to an assessment process.
Modular Software and Hardware
Several operators proposed modular hardware and software that reduces hardware costs, improves 
configuration exports across vendors, and makes software replacement easier without replacing the 
underlying hardware. Software modularity proposals were always paired with containerization technology. 
Containerization is common in enterprise environments and helps mitigate service downtime during 
updates or software errors by quickly spinning up a new software container. 
Available Testing Environments
Secure communications protocols are developed and updated every few years. This creates an issue for 
customers and manufacturers, as the customer is often reluctant to adopt a new protocol, or new client 
software, unless a server is available to test against. Manufacturers do not frequently allocate resources to 
developing a server when there is no client demand, or software client available for testing. This is a 
circular dependency. Operators asked for clear testing infrastructure.
Considerations for Post-Quantum Cryptography
While this research does not directly address post-quantum cryptography (PQC), it is important to briefly 
discuss as a looming problem for secure communications adoption. PQC adoption in OT suffers from the 
same general adoption problems highlighted in this guidance. If technology is difficult to use, costly, or 
prone to causing downtime, then it is unlikely to be adopted. PQC raises the importance of crypto-agility, as 
it is likely that the PQC transition will need to occur during the lifespan of any products purchased in the 
2020s. The industry will also need to pay close attention to key exchange mechanisms, as the larger key￾space will significantly increase network utilization during key exchange. Network utilization affecting 
system availability is already a concern, but this is likely to exacerbate the limitations of older network 
infrastructure and endpoints, putting more pressure on integrators and manufacturers to simplify the initial 
key deployment.

---

Opportunity for Action
The long lifecycle of OT ensures that industry will be mitigating insecure-by-design legacy protocols for 
decades. Each usability improvement or positive interaction with a secure protocol shortens that tail. Both 
critical infrastructure organizations and OT manufacturers should take the observations from operators 
presented in this guidance and apply them to their own infrastructure, products, and security programs. 
Security usability studies can take many forms, from VoC research to metrics, like tracking how many users 
disable security features or measuring deployment times to identify bottlenecks. Regardless of the form, 
operators, integrators, vendors, and manufacturers all play a role in navigating to a Secure by Design future.
Conclusion 
Despite decades of availability, secure versions of industrial protocols remain underutilized in OT 
environments. CISA’s 2025 Secure by Demand for OT guidance highlights the critical need for secure 
communication, defined as communication with signing and/or encryption, that protects against threats 
like actor-in-the-middle attacks and unauthorized updates. Asset owners are motivated by ensuring 
the integrity and the authenticity of OT communications. However, widespread adoption of secure 
communications is hindered not by a lack of technical solutions but by real-world barriers in cost, 
complexity, and operational risk.
Cost is driven by high procurement costs and licensing fees for secure-capable components and then 
exacerbated by complex solutions driving operators towards external assistance to deploy and maintain 
secure infrastructure. Complexity is increased for operators by poor integrator contracts, proprietary 
protocols, and unclear manufacturer guidance. Operational risk is driven by concerns over visibility, legacy 
infrastructure limitations, and interoperability issues. Appendix A summarizes the recommendations for 
operators and manufacturers to reduce these barriers. This research shows that operators desire the 
benefits of secure communication. Manufacturers and integrators need to factor in the usability of security 
to make that operator desire a reality. 
Acknowledgements
CISA conducted this research in partnership with representatives from:
 Anybus
 DNP Users Group
 National Security Agency
 ODVA
 OPC Foundation
 Rockwell Automation
 Schneider Electric
 The Modbus Organization
 Xylem

---

Appendix A. Summary of Recommendations
Recommendations for Owners and Operators
Owners and operators should: 
 Utilize signing on all communications in the OT environment and utilize encryption as needed to 
protect sensitive information (e.g., passwords, key exchanges, logic updates).
 If concerned with limiting visibility or poor key management causing downtime, consider a phased 
approach beginning with signing only and not dropping packets. 
 Search for products which support crypto-agility, the ability to replace and adapt cryptographic 
algorithms, to ensure the lifetime of the product is matched by the lifetime of the cryptographic 
algorithm. 
 Seek out vendor solutions that simplify secure workflows (e.g., via management tools, wizards, 
system integrator support).
 Ensure that open standard protocol implementations are certified, including security aspects such 
as key exchange mechanisms.
 Prioritize secure communication in OT on remote access paths, communication between functional 
or network boundaries, and firmware uploads and logic changes to limit access to the OT network 
and mitigate the impact of malicious actors on the OT network.
 Seek out products that simplify the initial key provisioning, as well as system integrators that have 
experience setting up security infrastructure, such as PKI, for the selected OT protocol. 
 Seek secure discovery and provisioning capabilities to allow a certificate manager to quickly 
onboard new components.

---

Recommendations for OT Manufacturers
Manufacturers should:
 Include secure communication capabilities in OT components and protocols by default.
 For integrated systems, pre-configure the system to use secure communications.
 Drive out complexity to reduce costs; track KPIs associated with the usability of security features. 
 Maximize opportunities for asset owners to transition from legacy communication patterns.
 Provide clear upgrade paths for legacy infrastructure.
 Default to the secure option for all configurations, such as unique credentials, security logging, 
access control, communication, etc.
 Ensure products have a clear design preference for secure deployment and operations; guide the 
customer to that safe and secure state and away from risky operating models.
 Provide guidance to the customer for any required supporting infrastructure (e.g., PKI).
 Develop integrator-facing deployment guidance that enables secure communication by default.
○ Manufacturers can reduce deployment costs by minimizing the configuration gap between 
legacy (brownfield) systems and new (greenfield) secure installations; for example, by
standardizing interfaces, providing pre-configured templates, and offering integration support 
for common OT environments.
 Build systems with cryptographic agility to remove the fear of buying at the wrong time. 
 Be transparent with the cost of security infrastructure.
 Use open standards and interoperability testing and certification (wherever possible), increasing 
confidence that operations will not be disrupted.
○ In most instances, operators initially blamed the secure protocol, not the vendor, when facing 
interoperability challenges, which has a broad dampening effect on security. 
 Publish testing results that demonstrate minimum required network bandwidth for secure 
communications when paired with the resources of common products.