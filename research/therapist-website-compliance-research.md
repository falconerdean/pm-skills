# Therapist Website Compliance Research: HIPAA, Legal, and Ethical Requirements

**Research Date:** April 5, 2026
**Scope:** US-based therapist and mental health professional websites

---

## Table of Contents

1. [HIPAA Requirements for Therapist Websites](#1-hipaa-requirements-for-therapist-websites)
2. [Required Privacy Policies and Disclosures](#2-required-privacy-policies-and-disclosures)
3. [Informed Consent for Telehealth/Online Communication](#3-informed-consent-for-telehealthonline-communication)
4. [APA and NASW Ethical Guidelines for Online Presence](#4-apa-and-nasw-ethical-guidelines-for-online-presence)
5. [State Licensing Disclosure Requirements](#5-state-licensing-disclosure-requirements)
6. [ADA/Accessibility Requirements](#6-adaaccessibility-requirements)
7. [Good Faith Estimate / No Surprises Act](#7-good-faith-estimate--no-surprises-act)
8. [Common Compliance Mistakes](#8-common-compliance-mistakes)

---

## 1. HIPAA Requirements for Therapist Websites

### Who Must Comply

Not all therapists are HIPAA covered entities. A therapist is a covered entity only when they conduct electronic transactions for which HHS has adopted standards (eligibility checks, treatment authorizations, billing via health plans). A therapist who exclusively bills patients directly and never conducts these electronic transactions is **not** a HIPAA covered entity.

However, even non-covered-entity therapists must still comply with **state privacy and security laws**, which in many states impose requirements similar to or more stringent than HIPAA.

**Source:** [HIPAA for Therapists - HIPAA Journal (Updated 2026)](https://www.hipaajournal.com/hipaa-for-therapists/)

### Categories of HIPAA Coverage for Therapists

| Category | Description |
|----------|-------------|
| **Solo covered entity** | Works independently and conducts covered electronic transactions (e.g., bills health plans electronically) |
| **Hybrid covered entity** | Bills some clients directly and others through health plans; must maintain separate data handling |
| **Affiliated covered entity** | Legally separate entities under common ownership that designate as a single entity for HIPAA |
| **Business associate** | Provides services to/on behalf of a covered entity; must comply with Security Rule and Breach Notification Rule |
| **Employee of covered entity** | Must comply with employer's HIPAA policies and procedures |

**Source:** [HIPAA for Therapists - HIPAA Journal](https://www.hipaajournal.com/hipaa-for-therapists/)

### Website-Specific HIPAA Requirements

#### Contact Forms
- Standard contact forms (WordPress, Squarespace, Wix defaults) are **not HIPAA-compliant** because they typically send unencrypted emails
- If a prospective patient submits a contact form that does **not** include PHI, HIPAA email rules do not apply
- However, when potential clients describe symptoms, conditions, or treatment history in contact forms, that constitutes PHI and must be protected
- Contact forms that collect PHI must use **end-to-end encryption**
- The form provider must sign a **Business Associate Agreement (BAA)**

**Source:** [Are Client Contact Forms Regulated by HIPAA?](https://hipaacomplianthosting.com/are-client-contact-form-submissions-for-therapist-websites-regulated-by-hipaa/), [Brighter Vision - HIPAA Compliant Forms](https://www.brightervision.com/blog/hipaa-compliant-email-forms/)

#### Email Communication
- Unencrypted email is **never** HIPAA compliant for transmitting PHI
- Free email services (Gmail, Yahoo, Outlook.com) do **not** offer BAAs and cannot be used for PHI
- The email provider must sign a BAA
- Several states require **affirmative opt-in consent** before communicating with patients by email: Connecticut, Colorado, Texas, Tennessee, Virginia, Utah, Montana, Iowa, Indiana
- PHI should never be included in email subject lines
- Email disclaimers alone are **insufficient** for compliance

**Source:** [HIPAA Compliant Email for Therapists - HIPAA Journal](https://www.hipaajournal.com/hipaa-compliant-email-for-therapists/), [HIPAA Compliance for Email - HIPAA Journal](https://www.hipaajournal.com/hipaa-compliance-for-email/)

#### Scheduling Systems
- Online scheduling must route PHI through secure, HIPAA-compliant systems
- Patient interactions should use patient portals and secure messaging, not consumer email or text
- The scheduling platform vendor must sign a BAA

**Source:** [HIPAA Journal - Therapy Practice Management Software](https://www.hipaajournal.com/therapy-practice-management-software/)

#### Website Hosting
- If the website stores or transmits PHI (via forms, patient portals, etc.), the hosting provider must sign a BAA
- SSL/TLS encryption is required for all pages that handle PHI
- Access controls, audit logs, and backup procedures must be in place

**Source:** [How to Make a HIPAA-Compliant Website - Compliancy Group](https://compliancy-group.com/how-to-make-a-hipaa-compliant-website-guide/)

#### Business Associate Agreements (BAAs)
BAAs are required with **all** third-party vendors that create, receive, maintain, or transmit PHI on the therapist's behalf, including:
- Email providers
- Website hosting providers
- Contact form / intake form providers
- Scheduling software
- EHR/practice management systems
- Cloud storage providers
- Telehealth platforms
- Payment processors (if they access PHI)

**Source:** [HIPAA Compliance for Therapists - Compliancy Group](https://compliancy-group.com/hipaa-compliance-for-therapists/)

---

## 2. Required Privacy Policies and Disclosures

### Notice of Privacy Practices (NPP) - 45 CFR 164.520

Covered entities must develop and distribute a Notice of Privacy Practices that describes, in **plain language**:

1. How the covered entity may **use and disclose** PHI
2. The individual's **rights** with respect to their PHI and how to exercise those rights (including the right to complain to HHS and to the entity)
3. The covered entity's **legal duties** to protect privacy, including a statement that it is required by law to maintain the privacy of PHI
4. **Contact information** for further questions about privacy policies
5. An **effective date**

**Source:** [HHS - Notice of Privacy Practices for PHI](https://www.hhs.gov/hipaa/for-professionals/privacy/guidance/privacy-practices-for-protected-health-information/index.html)

### Website Posting Requirements

> "A covered entity must prominently post and make available its notice on any web site it maintains that provides information about its customer services or benefits."

This is a **federal requirement** under 45 CFR 164.520(c). The NPP must be:
- Prominently posted on the website
- Available to any person who asks for it
- Made available at the provider's office/facility for individuals to take
- Posted in a clear and prominent location at the facility

**Source:** [HHS - Notice of Privacy Practices](https://www.hhs.gov/hipaa/for-professionals/privacy/guidance/privacy-practices-for-protected-health-information/index.html)

### When to Provide the Notice

- To new patients: no later than the date of first service delivery
- Must make a **good faith effort** to obtain the individual's **written acknowledgment** of receipt
- If first service is provided electronically (e.g., via website): must send electronic notice automatically and contemporaneously
- In emergencies: provide as soon as reasonably practicable after the emergency ends
- Must revise and redistribute whenever there is a **material change** to privacy practices

**Source:** [HHS - Notice of Privacy Practices](https://www.hhs.gov/hipaa/for-professionals/privacy/guidance/privacy-practices-for-protected-health-information/index.html)

### Substance Use Disorder (SUD) Records Update

As of **February 16, 2026**, HIPAA covered entities are required to include information about **substance use disorder (SUD) patient records** in their Notice of Privacy Practices, per 42 CFR Part 2 alignment with HIPAA.

**Source:** [HIPAA Journal - HIPAA for Therapists](https://www.hipaajournal.com/hipaa-for-therapists/), [42 CFR Part 2 - HIPAA Journal](https://www.hipaajournal.com/42-cfr-part-2/)

### Website Privacy Policy (Separate from NPP)

In addition to the HIPAA Notice of Privacy Practices, therapist websites should also include a **website privacy policy** addressing:
- What data the website collects (cookies, analytics, form submissions)
- How website visitor data is used and shared
- Cookie policies and tracking technologies
- Third-party integrations (Google Analytics, Facebook Pixel, etc.)
- Data retention practices
- Contact information for privacy questions

This is required under various **state consumer privacy laws** (e.g., California CCPA/CPRA, Virginia CDPA, Colorado CPA) and is a best practice regardless.

### Model Notices

HHS provides model Notice of Privacy Practices templates at:
[HHS Model Notices of Privacy Practices](https://www.hhs.gov/hipaa/for-professionals/privacy/guidance/model-notices-privacy-practices/index.html)

---

## 3. Informed Consent for Telehealth/Online Communication

### Federal Guidance (HHS/HRSA)

Most states require obtaining a patient's official informed consent before providing treatment using telehealth. HHS guidance specifies the following steps for telebehavioral health informed consent:

1. **Reassure privacy**: Confirm that information shared during the session is private
2. **Minor confidentiality**: Discuss with children/adolescents that they can share confidential information and it will not be shared with parents/guardians
3. **Disclosure exceptions**: Outline rare circumstances when information may be shared
4. **Information access**: Explain what records you do and do not have access to (EHR, state PDMP)
5. **SUD information**: Explain that substance use disorder information will not be included in their medical record without additional consent
6. **Private environment**: Discuss the importance of finding a private, quiet place for the appointment; suggest headphones if needed
7. **Household awareness**: Confirm that other household members respect the patient's need for privacy
8. **Additional consent for SUD providers**: If you screen, diagnose, or treat substance use disorders, you need additional patient consent before sharing information with other providers

**Source:** [Telehealth.HHS.gov - Informed Consent for Telebehavioral Health](https://telehealth.hhs.gov/providers/best-practice-guides/telehealth-for-behavioral-health/preparing-patients-for-telebehavioral-health/informed-consent-for-telebehavioral-health)

### Consent Documentation Methods

Informed consent can be documented:
- **In writing** or **electronically** before the appointment
- Through **verbal consent** recorded at the beginning of each session
- If another person joins (caregiver, other provider), they must also provide consent

**Source:** [Telehealth.HHS.gov](https://telehealth.hhs.gov/providers/best-practice-guides/telehealth-for-behavioral-health/preparing-patients-for-telebehavioral-health/informed-consent-for-telebehavioral-health)

### State-Specific Requirements (Select Examples)

| State | Requirement |
|-------|-------------|
| **California** | Must inform patient prior to initial delivery of telehealth services; obtain verbal or written consent; document in patient record |
| **Kentucky** | Informed consent required for psychologists, social workers, marriage & family therapists, behavioral analysts, and others |
| **Louisiana** | Consent must address: contingency plans for technical failure, scheduling/structure of services, potential risks, privacy/confidentiality, communication between sessions, emergency protocols, coordination of care, referrals/termination, record keeping, billing, ethical/legal responsibilities across state lines |
| **Rhode Island** | Informed consent required specifically for email or text-based communication |
| **Texas** | Consent required for telehealth services; can be obtained at either originating or distant site |

**Source:** [CCHPCA - Consent Requirements](https://www.cchpca.org/topic/consent-requirements-medicaid-medicare/), [CCHPCA - State Telehealth Laws Fall 2025](https://www.cchpca.org/resources/state-telehealth-laws-and-reimbursement-policies-report-fall-2025/)

### Key Elements for Telehealth Informed Consent Forms

A comprehensive telehealth informed consent should address:
- What telehealth involves and how it differs from in-person care
- Benefits and potential risks (technical failures, privacy limitations)
- Patient and provider identification procedures
- Emergency protocols and local emergency contacts
- Technology requirements and troubleshooting
- Privacy and security measures in place
- Recording policies
- How to handle technical difficulties mid-session
- Right to withdraw consent at any time
- Applicable fees and billing practices
- State licensure and practice limitations

**Source:** [Health Law Alliance - Navigating Informed Consent in Telehealth](https://www.healthlawalliance.com/blog/navigating-informed-consent-requirements-in-telehealth-a-providers-guide), [NASW Assurance - Telehealth Informed Consent](https://naswassurance.org/pdf/telehealth-informed-consent.pdf)

---

## 4. APA and NASW Ethical Guidelines for Online Presence

### APA Ethics Code - Standard 5: Advertising and Other Public Statements

#### Standard 5.01: Avoidance of False or Deceptive Statements
- Psychologists must not make **false, deceptive, or fraudulent** public statements about their practice, research, or work
- "Public statements" includes: advertising (paid or unpaid), product endorsements, brochures, printed matter, directory listings, resumes, media comments, lectures, published materials, and **website content**
- Must not misrepresent: training, competence, academic credentials, professional affiliations, service descriptions, clinical results/success rates, fees, or research findings
- May only claim degrees as credentials for health services if they were earned from a regionally accredited institution or were the basis for state licensure

#### Standard 5.02: Statements by Others
- Psychologists retain **professional responsibility** for promotional statements made on their behalf by others (including website designers, marketing agencies, or SEO consultants)
- Cannot compensate media personnel for publicity disguised as news

#### Standard 5.04: Media Presentations
- When providing public advice via print, Internet, or electronic transmission, statements must be:
  1. Based on professional knowledge, training, or experience
  2. Consistent with the Ethics Code
  3. Must **not indicate that a professional relationship exists** with the recipient
- This directly applies to blog posts, educational content, and advice on therapist websites

#### Standard 5.05: Testimonials
- Psychologists **cannot solicit testimonials** from current therapy clients or others who are vulnerable to undue influence
- This impacts the common practice of displaying client testimonials on websites

#### Standard 5.06: In-Person Solicitation
- Direct, uninvited solicitation of potential therapy clients is prohibited
- Exception: disaster outreach is permissible

**Source:** [APA Ethical Principles of Psychologists and Code of Conduct](https://www.apa.org/ethics/code), [APA Ethics Code 2017 PDF](https://www.apa.org/ethics/code/ethics-code-2017.pdf)

### NASW Code of Ethics - Technology-Related Standards

The 2021 revised NASW Code of Ethics includes explicit guidance on technology:

#### Preamble Update
"With growth in the use of communication technology in various aspects of social work practice, social workers need to be aware of the unique challenges that may arise in relation to the maintenance of confidentiality, informed consent, professional boundaries, professional competence, record keeping, and other ethical considerations. In general, all ethical standards in this Code of Ethics are applicable to interactions, relationships, or communications, whether they occur in person or with the use of technology."

#### Standard 1.06(e) - Electronic Communication Boundaries
- Social workers should **not** communicate with clients using technology for personal or non-work-related purposes

#### Standard 1.06(f) - Online Personal Information
- Social workers should be aware that posting personal information on professional websites or other media could cause **boundary confusion**, inappropriate dual relationships, or harm to clients

#### Standard 1.07 - Privacy and Confidentiality
- Social workers must take **reasonable steps** to protect confidentiality of electronic communications
- Must use applicable safeguards: encryption, firewalls, and passwords when using electronic systems

**Source:** [NASW Code of Ethics - English](https://www.socialworkers.org/About/Ethics/Code-of-Ethics/Code-of-Ethics-English), [New NASW Code of Ethics Standards for the Digital Age - Social Work Today](https://www.socialworktoday.com/archive/081617.shtml)

### NASW/ASWB/CSWE/CSWA Standards for Technology in Social Work Practice (2017)

This joint standards document covers:

1. **Provision of Information to the Public**: Standards on ethics/values and representation of self/accuracy of information online
2. **Designing and Delivering Services**: Ethical use of technology to deliver services, services requiring licensure, laws governing provision of services
3. **Informed Consent**: Benefits and risks of electronic social work services
4. **Confidentiality and Privacy**: Safeguards for electronic communications
5. **Boundary Considerations**: Managing online presence and dual relationships

**Source:** [NASW - Standards for Technology in Social Work Practice](https://www.socialworkers.org/Practice/NASW-Practice-Standards-Guidelines/Standards-for-Technology-in-Social-Work-Practice)

### Practical Implications for Websites

| Requirement | APA | NASW |
|-------------|-----|------|
| No false/misleading claims about credentials | Yes (5.01) | Yes (4.06) |
| No solicitation of testimonials from current clients | Yes (5.05) | Yes |
| Maintain boundaries in online presence | Implied | Yes (1.06e, 1.06f) |
| Responsible for third-party marketing content | Yes (5.02) | Yes |
| Blog/advice content must not imply therapeutic relationship | Yes (5.04) | Yes |
| Must use encryption for electronic communications | Implied via HIPAA | Yes (1.07) |

---

## 5. State Licensing Disclosure Requirements

### General Requirements

Most states require therapists to:
- Use their **correct licensed title** (e.g., LCSW, LMFT, LPC, LP)
- Display **credentials after their name** on all professional materials including websites
- Provide a **Professional Disclosure Statement** to prospective clients before engaging in counseling

Requirements vary significantly by state. Below are specific examples from states with well-documented requirements.

### California (BBS - Board of Behavioral Sciences)

Effective **July 1, 2025** (SB 1024), all licensees and registrants must:
- Include their **license or registration number** in all advertisements
- Provide their license/registration number and type when initiating telehealth services
- The "Notice to Clients" must contain:
  - Full name as filed with the Board
  - License or registration number
  - Type of license or registration (e.g., "Licensed Marriage and Family Therapist," "Associate Clinical Social Worker")
  - Expiration date of license or registration

**Source:** [California BBS - SB 1024 FAQ](https://www.bbs.ca.gov/pdf/required_notice_to_consumers_sb_1024.pdf), [California BBS - License Display Requirements](https://www.bbs.ca.gov/pdf/agen_notice/2022/20221208_telehealth_item_vi.pdf)

### New York (NYSED Office of the Professions)

- May only refer to yourself as "licensed" if you are licensed **and registered** with the State Education Department
- May advertise national certifications (e.g., "Board-Certified Music Therapist," "National Certified Counselor") only if documentable
- Practitioners with doctorates must clearly indicate their field when using "Doctor" in professional service offerings
- Cannot use professional credentials to imply superiority over unlicensed providers when offering non-licensed services (e.g., coaching)
- Undocumented specialty claims risk **unprofessional conduct charges**

**Source:** [NYSED - Advertising and Specialty Credentials for Mental Health Practitioners](https://www.op.nysed.gov/professions/mental-health-practitioners/professional-practice/advertising-and-specialty-credentials)

### Best Practices for All States

Regardless of specific state requirements, therapist websites should display:
- **Full name** as registered with the licensing board
- **License type** (LCSW, LMFT, LPC, PsyD, PhD, etc.)
- **License number**
- **State of licensure** (especially important for telehealth providers serving multiple states)
- **Supervisory status** if applicable (e.g., "under supervision of [Name], [License]")
- **National certifications** only if verifiable
- **Educational credentials** accurately represented

**Source:** [TherapyRoute - Mental Health Licensing Guide 2025](https://www.therapyroute.com/article/mental-health-licensing-regulation-in-the-usa-2025-guide-by-therapyroute), [ACA - Licensure Requirements](https://www.counseling.org/resources/licensure-requirements)

---

## 6. ADA/Accessibility Requirements

### Legal Framework

The Americans with Disabilities Act (ADA) applies to therapist websites under **Title III** (businesses open to the public / "public accommodations"). The Department of Justice has consistently held that websites of public accommodations must be accessible to people with disabilities.

> "An inaccessible website can exclude people just as much as steps at an entrance to a physical location."

**Source:** [ADA.gov - Guidance on Web Accessibility and the ADA](https://www.ada.gov/resources/web-guidance/)

### Applicable Standard: WCAG 2.1 Level AA

While the ADA does not prescribe specific technical standards for private businesses (Title III), courts and enforcement agencies consistently reference **WCAG 2.1 Level AA** as the benchmark. The four core principles (POUR):

1. **Perceivable** - Content accessible via sight, sound, or alternative formats
2. **Operable** - Full navigation via keyboard; no seizure-inducing content
3. **Understandable** - Clear structure, simple language, properly labeled forms
4. **Robust** - Compatible with assistive technologies (screen readers, etc.)

**Note:** For state and local government websites (Title II), a final rule published April 24, 2024 formally adopts WCAG 2.1 Level AA, with compliance deadlines in **April 2026** for large entities and April 2027 for smaller ones.

**Source:** [ADA.gov - Web Guidance](https://www.ada.gov/resources/web-guidance/), [ADA.gov - 2024 Web Rule Fact Sheet](https://www.ada.gov/resources/2024-03-08-web-rule/)

### Specific Requirements for Therapist Websites

| Element | Requirement |
|---------|-------------|
| **Color contrast** | Minimum 4.5:1 ratio for normal text; 3:1 for large text |
| **Text size** | Minimum 16px recommended; must support browser zoom |
| **Alt text** | Descriptive alt text on all images (not just "image") |
| **Video captions** | Synchronized captions for all video content |
| **Keyboard navigation** | Full site navigable without a mouse; visible focus indicators |
| **Skip navigation** | "Skip to main content" links for screen readers |
| **Form accessibility** | Labels, clear instructions, ARIA attributes, error messages that identify and explain the error |
| **Heading hierarchy** | Proper H1, H2, H3 structure |
| **Mobile responsive** | No horizontal scrolling required |
| **PDF accessibility** | Intake forms and documents must be accessible or have accessible alternatives |
| **Telehealth portals** | Scheduling and patient portals must be accessible |
| **No autoplay** | No autoplaying media that cannot be paused |

**Source:** [Mental Health IT Solutions - ADA Compliant Therapist Website](https://mentalhealthitsolutions.com/blog/ada-compliant-therapist-website/)

### Heightened Risk for Healthcare Websites

Healthcare websites, including therapist sites, are held to **higher standards** due to the vulnerable populations they serve. ADA compliance is not achieved through a single plugin or overlay; courts have repeatedly ruled that **overlays alone are insufficient**.

### Testing and Implementation

**Recommended testing tools:**
- WAVE Accessibility Tool
- Lighthouse Accessibility Audit (Chrome DevTools)
- WebAIM Contrast Checker
- NVDA / VoiceOver screen reader manual testing

**Typical remediation cost:** $500 - $2,000 depending on platform and number of issues.

**Source:** [Mental Health IT Solutions - ADA Compliance Guide](https://mentalhealthitsolutions.com/blog/ada-compliance-for-therapist-websites/), [Accessibility.Works - 2025 ADA Standards](https://www.accessibility.works/blog/wcag-ada-website-compliance-standards-requirements)

---

## 7. Good Faith Estimate / No Surprises Act

### Overview

The No Surprises Act (effective January 1, 2022) requires healthcare providers -- including therapists -- to provide a **Good Faith Estimate (GFE)** of expected charges to uninsured, out-of-network, or self-pay patients. This is particularly relevant for therapists since many operate on a self-pay/out-of-network model.

### Website Posting Requirement

Providers must prominently display a notice informing uninsured or self-pay patients of their right to receive a Good Faith Estimate. This notice must be:

- **Prominently displayed** on the provider's website
- Posted in the office and on-site where scheduling occurs
- Available in **accessible formats** and in the **language(s)** spoken by patients
- Clear, understandable written language

**Source:** [AAMFT - No Surprises Act Billing Disclosures](https://www.aamft.org/AAMFT/enhance_knowledge/No_Surprises_Act.aspx), [APA Services - Understanding the No Surprises Act](https://www.apaservices.org/practice/legal/managed/no-surprises-act)

### When to Provide the GFE

| Scenario | Deadline |
|----------|----------|
| Service scheduled **at least 3 days** in advance | No later than **1 business day** after scheduling |
| Service scheduled **at least 10 days** in advance | No later than **3 business days** after scheduling |
| Patient requests an estimate (no service scheduled) | No later than **3 business days** after the request |

### What the GFE Must Include

- Patient name and date of birth
- Description of the primary service/item
- Expected charges for the primary service/item
- Itemized list of expected services/items
- Provider name, NPI, and TIN
- Diagnosis codes (if applicable)
- Location where services will be provided
- A disclaimer that the GFE is an estimate, not a contract
- Notice that the patient can dispute bills exceeding the GFE by $400 or more

### Who It Applies To

The GFE requirement applies to:
- **Uninsured patients** (no health coverage at all)
- **Self-pay patients** (have insurance but choose not to use it)
- **Out-of-network patients** who will not be submitting claims

Marriage and family therapists, psychologists, licensed clinical social workers, licensed professional counselors, and psychiatrists all meet the definition of "provider" under the Act.

**Source:** [APA Services - No Surprises Act](https://www.apaservices.org/practice/legal/managed/no-surprises-act), [Headway - Good Faith Estimate Template](https://headway.co/resources/good-faith-estimate-template-for-therapists), [Psychiatry.org - No Surprises Act Implementation](https://www.psychiatry.org/psychiatrists/practice/practice-management/no-surprises-act-implementation)

### Dispute Resolution

If actual charges exceed the GFE by **$400 or more**, the patient has the right to initiate a dispute resolution process. APA recommends tracking patient billing against GFEs to avoid triggering this threshold.

**Source:** [APA Services - No Surprises Act](https://www.apaservices.org/practice/legal/managed/no-surprises-act)

---

## 8. Common Compliance Mistakes

### HIPAA / Privacy Mistakes

1. **Using standard (non-encrypted) contact forms**: Default WordPress, Squarespace, or Wix contact forms send data as unencrypted email. If clients include health information, this violates HIPAA.

2. **Using free/personal email for client communication**: Gmail, Yahoo, and Outlook.com do not sign BAAs. They cannot be used for PHI regardless of disclaimers added.

3. **Relying on email disclaimers**: Adding "This email may contain confidential information" disclaimers does not make email HIPAA-compliant and can actually make a data breach worse.

4. **No BAAs with vendors**: Using scheduling platforms, form builders, email services, or cloud storage without executed BAAs.

5. **No Notice of Privacy Practices on website**: Covered entities must prominently post the NPP on any website that provides information about services.

6. **Failing to appoint a Privacy/Security Officer**: Even solo practitioners need a designated individual responsible for HIPAA compliance.

7. **No documented risk assessment**: HIPAA requires regular (at minimum annual) security risk assessments.

8. **Mixing psychotherapy notes with medical records**: Psychotherapy notes receive additional protections and must be stored separately.

**Source:** [Hushmail - HIPAA for Therapists Guide](https://blog.hushmail.com/blog/hipaa-therapists), [SimplePractice - HIPAA Compliant Email](https://www.simplepractice.com/blog/hipaa-compliant-email-for-therapists/), [Brighter Vision - HIPAA Compliant Forms](https://www.brightervision.com/blog/hipaa-compliant-email-forms/)

### Advertising / Ethical Mistakes

9. **Displaying client testimonials**: APA Standard 5.05 prohibits soliciting testimonials from current clients or those vulnerable to undue influence. Social workers face similar restrictions. Many therapists display Google reviews or testimonials without considering this.

10. **Overstating credentials or specialties**: Claiming expertise in areas without adequate training (e.g., "EMDR specialist" without EMDRIA certification) violates APA 5.01 and state licensing board rules.

11. **Using "Doctor" without clarification**: Practitioners with non-medical doctorates must specify their field when using the title "Doctor" in professional contexts (e.g., "Dr. Smith, PsyD" not just "Dr. Smith").

12. **Implying a therapeutic relationship through website content**: Blog posts or advice columns that are too personalized can violate APA 5.04, which prohibits implying a professional relationship with recipients.

**Source:** [APA Ethics Code](https://www.apa.org/ethics/code), [NYSED Advertising Guidelines](https://www.op.nysed.gov/professions/mental-health-practitioners/professional-practice/advertising-and-specialty-credentials)

### Good Faith Estimate Mistakes

13. **No GFE notice posted on website**: The No Surprises Act requires prominent posting of the GFE notice on websites.

14. **Not providing GFE to self-pay clients**: Even if a client has insurance but chooses not to use it, they are entitled to a GFE.

15. **Missing the timing deadlines**: Failing to provide the GFE within the required business-day windows.

**Source:** [APA Services - No Surprises Act](https://www.apaservices.org/practice/legal/managed/no-surprises-act)

### Accessibility Mistakes

16. **Low contrast text**: Especially common with muted/calming therapy color schemes that sacrifice readability.

17. **Missing alt text on images**: Particularly on headshots, office photos, and decorative images.

18. **Inaccessible intake forms/PDFs**: PDF intake packets that cannot be read by screen readers.

19. **No keyboard navigation**: Sites that require mouse interaction for scheduling or form completion.

20. **Using accessibility overlays as the sole solution**: Courts have ruled that automated overlay plugins are insufficient for ADA compliance.

**Source:** [Mental Health IT Solutions - ADA Compliance](https://mentalhealthitsolutions.com/blog/ada-compliant-therapist-website/), [ADA.gov - Web Guidance](https://www.ada.gov/resources/web-guidance/)

### Telehealth Consent Mistakes

21. **No written informed consent for telehealth**: Many therapists began offering telehealth during COVID-19 without implementing proper consent procedures that may have been waived under emergency orders (now expired).

22. **Not addressing state-specific requirements**: Telehealth consent requirements vary by state; using a generic form may miss required elements (e.g., Louisiana's extensive list of required disclosures).

23. **Failing to discuss emergency protocols**: Not establishing local emergency contacts for remote clients.

**Source:** [Telehealth.HHS.gov - Informed Consent](https://telehealth.hhs.gov/providers/best-practice-guides/telehealth-for-behavioral-health/preparing-patients-for-telebehavioral-health/informed-consent-for-telebehavioral-health), [CCHPCA - Consent Requirements](https://www.cchpca.org/topic/consent-requirements-medicaid-medicare/)

---

## Compliance Checklist Summary

### Must-Have Items for a Therapist Website

- [ ] **SSL certificate** (HTTPS) on all pages
- [ ] **Notice of Privacy Practices** posted prominently (if covered entity)
- [ ] **Website privacy policy** addressing cookies, analytics, data collection
- [ ] **Good Faith Estimate notice** posted prominently for self-pay/uninsured patients
- [ ] **License credentials displayed**: full name, license type, license number, state
- [ ] **HIPAA-compliant contact form** (encrypted, with vendor BAA) -- or form that explicitly states "Do not include health information"
- [ ] **HIPAA-compliant email** (with BAA) for any client communications containing PHI
- [ ] **Telehealth informed consent** form/process documented
- [ ] **No client testimonials** from current or recent clients (APA 5.05)
- [ ] **Accurate credential representations** -- no false or misleading claims
- [ ] **ADA-accessible design**: WCAG 2.1 AA compliance
- [ ] **Accessible intake forms** (PDF or online)
- [ ] **BAAs executed** with all technology vendors handling PHI
- [ ] **Emergency contact protocols** documented for telehealth clients

---

## Key Source URLs

### Government / Regulatory
- [HHS HIPAA for Professionals](https://www.hhs.gov/hipaa/for-professionals/index.html)
- [HHS Notice of Privacy Practices](https://www.hhs.gov/hipaa/for-professionals/privacy/guidance/privacy-practices-for-protected-health-information/index.html)
- [HHS Model Notices](https://www.hhs.gov/hipaa/for-professionals/privacy/guidance/model-notices-privacy-practices/index.html)
- [HHS Summary of Privacy Rule](https://www.hhs.gov/hipaa/for-professionals/privacy/laws-regulations/index.html)
- [Telehealth.HHS.gov - Informed Consent](https://telehealth.hhs.gov/providers/best-practice-guides/telehealth-for-behavioral-health/preparing-patients-for-telebehavioral-health/informed-consent-for-telebehavioral-health)
- [ADA.gov - Web Accessibility Guidance](https://www.ada.gov/resources/web-guidance/)
- [ADA.gov - 2024 Title II Web Rule](https://www.ada.gov/resources/2024-03-08-web-rule/)

### Professional Associations
- [APA Ethics Code](https://www.apa.org/ethics/code)
- [APA Services - No Surprises Act](https://www.apaservices.org/practice/legal/managed/no-surprises-act)
- [APA HIPAA Privacy Rule FAQ](https://www.apaservices.org/practice/business/hipaa/faq)
- [NASW Code of Ethics](https://www.socialworkers.org/About/Ethics/Code-of-Ethics/Code-of-Ethics-English)
- [NASW Technology Standards](https://www.socialworkers.org/Practice/NASW-Practice-Standards-Guidelines/Standards-for-Technology-in-Social-Work-Practice)
- [AAMFT - No Surprises Act](https://www.aamft.org/AAMFT/enhance_knowledge/No_Surprises_Act.aspx)
- [NYSED - Advertising Guidelines](https://www.op.nysed.gov/professions/mental-health-practitioners/professional-practice/advertising-and-specialty-credentials)

### Compliance Guidance
- [HIPAA Journal - HIPAA for Therapists](https://www.hipaajournal.com/hipaa-for-therapists/)
- [HIPAA Journal - Compliant Email for Therapists](https://www.hipaajournal.com/hipaa-compliant-email-for-therapists/)
- [Compliancy Group - HIPAA Compliant Website Guide](https://compliancy-group.com/how-to-make-a-hipaa-compliant-website-guide/)
- [Compliancy Group - HIPAA for Therapists](https://compliancy-group.com/hipaa-compliance-for-therapists/)
- [Hushmail - HIPAA for Therapists Guide](https://blog.hushmail.com/blog/hipaa-therapists)
- [SimplePractice - HIPAA Compliant Email](https://www.simplepractice.com/blog/hipaa-compliant-email-for-therapists/)
- [Mental Health IT Solutions - ADA Compliance](https://mentalhealthitsolutions.com/blog/ada-compliant-therapist-website/)

### Telehealth Policy
- [CCHPCA - Consent Requirements](https://www.cchpca.org/topic/consent-requirements-medicaid-medicare/)
- [CCHPCA - State Telehealth Laws Fall 2025](https://www.cchpca.org/resources/state-telehealth-laws-and-reimbursement-policies-report-fall-2025/)
- [Health Law Alliance - Informed Consent Guide](https://www.healthlawalliance.com/blog/navigating-informed-consent-requirements-in-telehealth-a-providers-guide)

### State Licensing
- [California BBS - SB 1024 Notice Requirements](https://www.bbs.ca.gov/pdf/required_notice_to_consumers_sb_1024.pdf)
- [NYSED - Mental Health Practitioner Advertising](https://www.op.nysed.gov/professions/mental-health-practitioners/professional-practice/advertising-and-specialty-credentials)
- [ACA - Licensure Requirements by State](https://www.counseling.org/resources/licensure-requirements)
