const categoryStyles: Record<string, string> = {
  Billing: 'category-billing',
  Refund: 'category-refund',
  'Technical Issue': 'category-technical',
  'Payment Issue': 'category-payment',
  'Order / Delivery': 'category-order',
  'Account Access': 'category-access',
  'Account Management': 'category-account',
  'Security / Fraud': 'category-security',
  'General Inquiry': 'category-general',
  Greeting: 'category-greeting',
  Thanks: 'category-greeting',
  'Greeting/Thanks': 'category-greeting',
  'Greeting / Thanks': 'category-greeting',
  'Out of Scope': 'category-outscope',
}

export function categoryClassName(category: string) {
  return categoryStyles[category] || 'category-general'
}
