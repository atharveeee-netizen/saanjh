// UI strings for the field and household surfaces in English, Hindi and Marathi.
// The Hindi and Marathi text is machine translation and is marked for review by a
// native speaker before any field use (see REVIEW_NOTE).

export type Lang = "en" | "hi" | "mr";
export const LANGS: { value: Lang; label: string }[] = [
  { value: "en", label: "English" }, { value: "hi", label: "हिंदी" }, { value: "mr", label: "मराठी" },
];
export const REVIEW_NOTE = "Hindi and Marathi text is machine translation, awaiting review by a native speaker.";

type Dict = Record<string, string>;
const en: Dict = {
  today: "Today", enrol: "Enrol", install: "Install", battery: "Battery", payouts: "Payouts",
  next_window: "Next deficit window", homes_to_call: "Homes to call or visit", open_complaints: "Open complaints",
  battery_status: "Community battery", charged: "charged", offline_sync: "changes waiting to sync",
  synced: "All changes synced", consent: "Consent", consent_read: "I read the consent aloud in the household's language",
  record_consent: "Attach consent recording", segment: "Household type", critical: "Critical load",
  critical_reason: "Reason (medical device, shop fridge)", nameplate: "Inverter nameplate photo",
  meter_no: "Smart meter number", save_enrol: "Enrol household", enrolled: "Household enrolled",
  enrolled_body: "Saved on this phone. It will sync when the network returns.",
  install_title: "Install relay node", install_done: "Installation recorded", record_install: "Record installation",
  step_isolate: "Switch off the inverter's mains input at the MCB and confirm with a tester",
  step_nc: "Check the relay is normally closed: with the node unpowered, mains reaches the inverter",
  step_wire: "Wire the relay in series with the inverter's mains input and close the cover",
  step_test: "Power the node, run the test from the app: inverter goes to battery, then back to mains",
  step_photo: "Take a photo of the finished installation",
  temperature: "Temperature", alarms: "Alarms", none: "None", last_inspection: "Last inspection",
  next_maintenance: "Next maintenance due", credits_month: "Credits earned this month", operator_fee: "Your fee this month",
  home_on: "Your home is on.", essentials_until: "Essentials only until", what_fits: "What fits in your band",
  battery_kept: "Your inverter battery is kept above 70% for your own backup.", credits: "Credits",
  low_income: "Low-income", middle: "Middle", affluent: "Affluent", select: "Select",
};
const hi: Dict = {
  today: "आज", enrol: "नामांकन", install: "इंस्टॉल", battery: "बैटरी", payouts: "भुगतान",
  next_window: "अगली कमी की अवधि", homes_to_call: "जिन घरों को कॉल या विज़िट करना है", open_complaints: "खुली शिकायतें",
  battery_status: "सामुदायिक बैटरी", charged: "चार्ज", offline_sync: "बदलाव सिंक होने बाकी",
  synced: "सभी बदलाव सिंक हो गए", consent: "सहमति", consent_read: "मैंने परिवार की भाषा में सहमति पढ़कर सुनाई",
  record_consent: "सहमति की रिकॉर्डिंग जोड़ें", segment: "घर का प्रकार", critical: "ज़रूरी लोड",
  critical_reason: "कारण (मेडिकल उपकरण, दुकान का फ्रिज)", nameplate: "इन्वर्टर नेमप्लेट की फोटो",
  meter_no: "स्मार्ट मीटर नंबर", save_enrol: "घर का नामांकन करें", enrolled: "घर का नामांकन हो गया",
  enrolled_body: "इस फोन में सेव हो गया। नेटवर्क आने पर सिंक होगा।",
  install_title: "रिले नोड लगाएँ", install_done: "इंस्टॉलेशन दर्ज हुआ", record_install: "इंस्टॉलेशन दर्ज करें",
  step_isolate: "इन्वर्टर की मेन सप्लाई MCB से बंद करें और टेस्टर से जाँचें",
  step_nc: "जाँचें कि रिले नॉर्मली क्लोज़्ड है: नोड बंद होने पर भी इन्वर्टर तक मेन सप्लाई पहुँचे",
  step_wire: "रिले को इन्वर्टर की मेन सप्लाई के साथ सीरीज़ में जोड़ें और कवर बंद करें",
  step_test: "नोड चालू करें, ऐप से टेस्ट चलाएँ: इन्वर्टर बैटरी पर जाए, फिर मेन पर लौटे",
  step_photo: "पूरे इंस्टॉलेशन की फोटो लें",
  temperature: "तापमान", alarms: "अलार्म", none: "कोई नहीं", last_inspection: "पिछला निरीक्षण",
  next_maintenance: "अगला रखरखाव", credits_month: "इस महीने के क्रेडिट", operator_fee: "इस महीने आपकी फीस",
  home_on: "आपके घर में बिजली है।", essentials_until: "तक सिर्फ़ ज़रूरी उपकरण", what_fits: "आपकी सीमा में क्या चल सकता है",
  battery_kept: "आपकी इन्वर्टर बैटरी आपके अपने बैकअप के लिए 70% से ऊपर रखी जाती है।", credits: "क्रेडिट",
  low_income: "कम आय", middle: "मध्यम", affluent: "संपन्न", select: "चुनें",
};
const mr: Dict = {
  today: "आज", enrol: "नोंदणी", install: "बसवणे", battery: "बॅटरी", payouts: "देयके",
  next_window: "पुढील तुटवड्याची वेळ", homes_to_call: "ज्या घरांना फोन किंवा भेट द्यायची", open_complaints: "प्रलंबित तक्रारी",
  battery_status: "सामुदायिक बॅटरी", charged: "चार्ज", offline_sync: "बदल सिंक व्हायचे बाकी",
  synced: "सर्व बदल सिंक झाले", consent: "संमती", consent_read: "मी कुटुंबाच्या भाषेत संमती वाचून दाखवली",
  record_consent: "संमतीचे रेकॉर्डिंग जोडा", segment: "घराचा प्रकार", critical: "अत्यावश्यक भार",
  critical_reason: "कारण (वैद्यकीय उपकरण, दुकानाचा फ्रिज)", nameplate: "इन्व्हर्टर नेमप्लेटचा फोटो",
  meter_no: "स्मार्ट मीटर क्रमांक", save_enrol: "घराची नोंदणी करा", enrolled: "घराची नोंदणी झाली",
  enrolled_body: "या फोनवर जतन झाले. नेटवर्क आल्यावर सिंक होईल.",
  install_title: "रिले नोड बसवा", install_done: "बसवणी नोंदवली", record_install: "बसवणी नोंदवा",
  step_isolate: "इन्व्हर्टरचा मेन पुरवठा MCB वरून बंद करा आणि टेस्टरने तपासा",
  step_nc: "रिले नॉर्मली क्लोज्ड आहे ते तपासा: नोड बंद असतानाही इन्व्हर्टरला मेन पुरवठा मिळतो",
  step_wire: "रिले इन्व्हर्टरच्या मेन पुरवठ्यासोबत सिरीजमध्ये जोडा आणि कव्हर बंद करा",
  step_test: "नोड सुरू करा, ॲपमधून चाचणी करा: इन्व्हर्टर बॅटरीवर जातो, मग मेनवर परततो",
  step_photo: "पूर्ण बसवणीचा फोटो घ्या",
  temperature: "तापमान", alarms: "अलार्म", none: "काहीही नाही", last_inspection: "मागील तपासणी",
  next_maintenance: "पुढील देखभाल", credits_month: "या महिन्याचे क्रेडिट", operator_fee: "या महिन्याचे तुमचे मानधन",
  home_on: "तुमच्या घरी वीज सुरू आहे.", essentials_until: "पर्यंत फक्त आवश्यक उपकरणे", what_fits: "तुमच्या मर्यादेत काय चालेल",
  battery_kept: "तुमची इन्व्हर्टर बॅटरी तुमच्या स्वतःच्या बॅकअपसाठी 70% च्या वर ठेवली जाते.", credits: "क्रेडिट",
  low_income: "कमी उत्पन्न", middle: "मध्यम", affluent: "संपन्न", select: "निवडा",
};
const DICTS: Record<Lang, Dict> = { en, hi, mr };
export const t = (lang: Lang, key: string) => DICTS[lang][key] ?? en[key] ?? key;
