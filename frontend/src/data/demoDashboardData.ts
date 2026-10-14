export interface DashboardSummary {
  transactions_analyzed: number;
  fraud_detected: number;
  legitimate_transactions: number;
  fraud_rate: number;
  amount_at_risk: number;
  total_amount_analyzed: number;
  confirmed_fraud_cases: number;
  open_cases_count: number;
  risk_distribution: Record<string, number>;
  domain_breakdown: Record<string, number>;
  avg_inference_latency_ms: number;
  timeline: { time: string; total: number; legitimate: number; fraud: number; suspicious: number }[];
  timeline_range: string;
}

export interface TxRow {
  id: number;
  timestamp: string | null;
  type: string;
  domain_label: string;
  amount: number | null;
  fraud_probability: number;
  risk_level: string;
  prediction: string;
  recommended_action: string;
  inference_latency_ms: number;
}

export interface TxPage {
  page: number;
  page_size: number;
  total: number;
  pages: number;
  results: TxRow[];
}

export interface AlertItem {
  id: number;
  timestamp: string | null;
  type: string;
  domain_label: string;
  risk_level: string;
  fraud_probability: number;
  prediction: string;
  recommended_action: string;
}

export const DEMO_SUMMARY: DashboardSummary = {
  transactions_analyzed: 44,
  fraud_detected: 24,
  legitimate_transactions: 20,
  fraud_rate: 54.55,
  amount_at_risk: 11595150,
  total_amount_analyzed: 12121874,
  confirmed_fraud_cases: 2,
  open_cases_count: 24,
  risk_distribution: {
    HIGH: 22,
    LOW: 15,
    MEDIUM: 7,
  },
  domain_breakdown: {
    PaySim: 23,
    UPI: 7,
    "SMS Spam": 4,
    Bitcoin: 4,
    "Bank Transfer": 2,
    "Email Phishing": 2,
    "Credit Card": 1,
    "URL Phishing": 1,
  },
  avg_inference_latency_ms: 219.2,
  timeline: [
    { time: "00:00", total: 4, legitimate: 3, fraud: 1, suspicious: 0 },
    { time: "04:00", total: 2, legitimate: 2, fraud: 0, suspicious: 0 },
    { time: "08:00", total: 7, legitimate: 3, fraud: 3, suspicious: 1 },
    { time: "12:00", total: 14, legitimate: 5, fraud: 7, suspicious: 2 },
    { time: "16:00", total: 11, legitimate: 4, fraud: 5, suspicious: 2 },
    { time: "20:00", total: 6, legitimate: 3, fraud: 2, suspicious: 1 },
  ],
  timeline_range: "24h",
};

export const DEMO_ALERTS: AlertItem[] = [
  {
    id: 44,
    timestamp: new Date(Date.now() - 3600000 * 2).toISOString(),
    type: "TRANSFER",
    domain_label: "PaySim",
    prediction: "FRAUD",
    fraud_probability: 0.99,
    risk_level: "HIGH",
    recommended_action: "BLOCK",
  },
  {
    id: 43,
    timestamp: new Date(Date.now() - 3600000 * 5).toISOString(),
    type: "CASH_OUT",
    domain_label: "PaySim",
    prediction: "FRAUD",
    fraud_probability: 0.99,
    risk_level: "HIGH",
    recommended_action: "BLOCK",
  },
  {
    id: 41,
    timestamp: new Date(Date.now() - 3600000 * 12).toISOString(),
    type: "TRANSFER",
    domain_label: "PaySim",
    prediction: "FRAUD",
    fraud_probability: 0.99,
    risk_level: "HIGH",
    recommended_action: "BLOCK",
  },
  {
    id: 40,
    timestamp: new Date(Date.now() - 3600000 * 24).toISOString(),
    type: "TRANSFER",
    domain_label: "PaySim",
    prediction: "FRAUD",
    fraud_probability: 0.99,
    risk_level: "HIGH",
    recommended_action: "BLOCK",
  },
  {
    id: 39,
    timestamp: new Date(Date.now() - 3600000 * 28).toISOString(),
    type: "PAYMENT",
    domain_label: "UPI",
    prediction: "FRAUD",
    fraud_probability: 0.96,
    risk_level: "HIGH",
    recommended_action: "BLOCK",
  },
  {
    id: 38,
    timestamp: new Date(Date.now() - 3600000 * 32).toISOString(),
    type: "SMS",
    domain_label: "SMS Spam",
    prediction: "SPAM",
    fraud_probability: 0.92,
    risk_level: "HIGH",
    recommended_action: "BLOCK",
  },
  {
    id: 37,
    timestamp: new Date(Date.now() - 3600000 * 36).toISOString(),
    type: "TX",
    domain_label: "Bitcoin",
    prediction: "ILLICIT",
    fraud_probability: 0.88,
    risk_level: "HIGH",
    recommended_action: "BLOCK",
  },
];

export const DEMO_TRANSACTIONS: TxRow[] = [
  {
    id: 44,
    timestamp: new Date(Date.now() - 1000 * 60 * 15).toISOString(),
    domain_label: "PaySim",
    type: "TRANSFER",
    amount: 9800000,
    prediction: "FRAUD",
    fraud_probability: 0.99,
    risk_level: "HIGH",
    recommended_action: "BLOCK",
    inference_latency_ms: 210,
  },
  {
    id: 43,
    timestamp: new Date(Date.now() - 1000 * 60 * 45).toISOString(),
    domain_label: "PaySim",
    type: "CASH_OUT",
    amount: 1500000,
    prediction: "FRAUD",
    fraud_probability: 0.99,
    risk_level: "HIGH",
    recommended_action: "BLOCK",
    inference_latency_ms: 225,
  },
  {
    id: 42,
    timestamp: new Date(Date.now() - 1000 * 60 * 90).toISOString(),
    domain_label: "UPI",
    type: "PAYMENT",
    amount: 1250,
    prediction: "LEGITIMATE",
    fraud_probability: 0.05,
    risk_level: "LOW",
    recommended_action: "APPROVE",
    inference_latency_ms: 180,
  },
  {
    id: 41,
    timestamp: new Date(Date.now() - 1000 * 60 * 130).toISOString(),
    domain_label: "PaySim",
    type: "TRANSFER",
    amount: 250000,
    prediction: "FRAUD",
    fraud_probability: 0.99,
    risk_level: "HIGH",
    recommended_action: "BLOCK",
    inference_latency_ms: 215,
  },
  {
    id: 40,
    timestamp: new Date(Date.now() - 1000 * 60 * 200).toISOString(),
    domain_label: "Credit Card",
    type: "PURCHASE",
    amount: 4500,
    prediction: "LEGITIMATE",
    fraud_probability: 0.12,
    risk_level: "LOW",
    recommended_action: "APPROVE",
    inference_latency_ms: 195,
  },
  {
    id: 39,
    timestamp: new Date(Date.now() - 1000 * 60 * 310).toISOString(),
    domain_label: "SMS Spam",
    type: "SMS",
    amount: null,
    prediction: "SPAM",
    fraud_probability: 0.94,
    risk_level: "HIGH",
    recommended_action: "BLOCK",
    inference_latency_ms: 190,
  },
  {
    id: 38,
    timestamp: new Date(Date.now() - 1000 * 60 * 420).toISOString(),
    domain_label: "URL Phishing",
    type: "LINK",
    amount: null,
    prediction: "PHISHING",
    fraud_probability: 0.89,
    risk_level: "HIGH",
    recommended_action: "BLOCK",
    inference_latency_ms: 175,
  },
  {
    id: 37,
    timestamp: new Date(Date.now() - 1000 * 60 * 550).toISOString(),
    domain_label: "Bank Transfer",
    type: "WIRE",
    amount: 320000,
    prediction: "SUSPICIOUS",
    fraud_probability: 0.65,
    risk_level: "MEDIUM",
    recommended_action: "VERIFY",
    inference_latency_ms: 240,
  },
  {
    id: 36,
    timestamp: new Date(Date.now() - 1000 * 60 * 620).toISOString(),
    domain_label: "UPI",
    type: "PAYMENT",
    amount: 850,
    prediction: "LEGITIMATE",
    fraud_probability: 0.03,
    risk_level: "LOW",
    recommended_action: "APPROVE",
    inference_latency_ms: 160,
  },
  {
    id: 35,
    timestamp: new Date(Date.now() - 1000 * 60 * 750).toISOString(),
    domain_label: "Bitcoin",
    type: "TX",
    amount: 45000,
    prediction: "ILLICIT",
    fraud_probability: 0.87,
    risk_level: "HIGH",
    recommended_action: "BLOCK",
    inference_latency_ms: 230,
  },
];

export function getDemoTxPage(page = 1, search = "", risk = "ALL"): TxPage {
  let filtered = [...DEMO_TRANSACTIONS];
  if (risk && risk !== "ALL") {
    filtered = filtered.filter((t) => t.risk_level === risk);
  }
  if (search) {
    const q = search.toLowerCase();
    filtered = filtered.filter(
      (t) =>
        t.domain_label.toLowerCase().includes(q) ||
        t.type.toLowerCase().includes(q) ||
        t.prediction.toLowerCase().includes(q)
    );
  }
  const pageSize = 15;
  const start = (page - 1) * pageSize;
  const results = filtered.slice(start, start + pageSize);
  return {
    total: filtered.length,
    page,
    page_size: pageSize,
    pages: Math.max(1, Math.ceil(filtered.length / pageSize)),
    results,
  };
}
