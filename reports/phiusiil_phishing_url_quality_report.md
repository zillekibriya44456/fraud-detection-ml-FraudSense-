# Data Quality Report: URL Phishing (PhiUSIIL)

**Dataset**: `data/raw/url_phishing/PhiUSIIL_Phishing_URL_Dataset.csv`  
**Domain**: URL Phishing Detection  
**Target Column**: `label` (1 = Phishing, 0 = Legitimate)  

## 1. Summary Statistics
- **Total Records**: 235,795
- **Total Columns**: 56
- **Missing Values**: 0 (0.00%)
- **URL Duplicates Removed**: 425
- **Post-Clean Total Records**: 235,370
- **Phishing URLs**: 134,850 (57.19%)
- **Legitimate URLs**: 100,945 (42.81%)
- **Class Balance**: 57.2% Phishing / 42.8% Legitimate (Well balanced)

## 2. Feature Structure
- **Identifier Strings (Dropped)**: `FILENAME`, `URL`, `Domain`, `TLD`, `Title`.
- **Lexical URL Features**: `URLLength`, `DomainLength`, `IsDomainIP`, `URLSimilarityIndex`, `CharContinuationRate`, `TLDLegitimateProb`, `URLCharProb`, `TLDLength`, `NoOfSubDomain`, `HasObfuscation`, `NoOfLettersInURL`, `LetterRatioInURL`, `NoOfDegitsInURL`, `DegitRatioInURL`, `NoOfEqualsInURL`, `NoOfQMarkInURL`, `NoOfAmpersandInURL`, `NoOfOtherSpecialCharsInURL`, `SpacialCharRatioInURL`, `IsHTTPS`.
- **Webpage Content & DOM Features**: `LineOfCode`, `LargestLineLength`, `HasTitle`, `DomainTitleMatchScore`, `URLTitleMatchScore`, `HasFavicon`, `Robots`, `IsResponsive`, `NoOfURLRedirect`, `NoOfSelfRedirect`, `HasDescription`, `NoOfPopup`, `NoOfiFrame`, `HasExternalFormSubmit`, `HasSocialNet`, `HasSubmitButton`, `HasHiddenFields`, `HasPasswordField`, `Bank`, `Pay`, `Crypto`, `HasCopyrightInfo`, `NoOfImage`, `NoOfCSS`, `NoOfJS`, `NoOfSelfRef`, `NoOfEmptyRef`, `NoOfExternalRef`.
