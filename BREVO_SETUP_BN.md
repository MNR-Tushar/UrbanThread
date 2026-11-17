# UrbanThread-এ Brevo email verification setup

প্রজেক্টের signup verification, resend, password reset, welcome এবং order email Brevo Transactional Email API দিয়ে পাঠানো যাবে। Free plan-এ দৈনিক ৩০০ email পাঠানো যায়; limit প্রতিদিন reset হয়। [Brevo Free plan limit](https://help.brevo.com/hc/en-us/articles/208580669-FAQs-What-are-the-limits-of-the-Free-plan)

## ১. Brevo account ও sender প্রস্তুত করুন

1. [Brevo](https://www.brevo.com/) account খুলে login/email verification এবং account setup শেষ করুন। Transactional Email সক্রিয় আছে কি না dashboard-এ দেখুন।
2. **Settings → Senders, Domains, IPs → Senders** থেকে sender যোগ করুন। `urbanthread/.env`-এ থাকা `BREVO_SENDER_EMAIL`-এর ঠিকানাটি verify করুন। আপনার নিজের domain-এর DNS edit করার অধিকার থাকলে production-এর জন্য domain authenticate করুন; না হলে অন্তত sender address verify করে account-এর deliverability status দেখুন।
3. **Settings → SMTP & API → API Keys & MCP → Create API key** থেকে API v3 key বানান। Key-টি একবারই পুরো দেখা যেতে পারে, তাই নিরাপদে কপি করুন। API key হলো `BREVO_API_KEY`; SMTP key নয়। API key `api-key` HTTP header দিয়ে পাঠানো হবে। [Brevo API key guide](https://help.brevo.com/hc/en-us/articles/209467485-Create-and-manage-your-API-keys)

Brevo sender অবশ্যই registered ও verified হতে হবে। [Brevo transactional email API guide](https://developers.brevo.com/docs/send-a-transactional-email)

## ২. `.env`-এ API key বসান

`urbanthread/.env` ফাইলে এই লাইনটি খুঁজুন:

```dotenv
BREVO_API_KEY=
```

`=`-এর পরে আপনার Brevo API key বসান:

```dotenv
BREVO_API_KEY=xkeysib-your-real-brevo-api-key
BREVO_SENDER_EMAIL=rahman23105101275@diu.edu.bd
BREVO_SENDER_NAME=UrbanThread
BREVO_API_TIMEOUT=15
```

`BREVO_API_KEY`-এ Brevo-র **API key** বসাবেন, SMTP key নয়। পুরো key কখনো GitHub, screenshot, chat বা log-এ শেয়ার করবেন না; `.env` Git-এ commit করবেন না। `BREVO_API_KEY` non-empty হলে settings স্বয়ংক্রিয়ভাবে Brevo backend বেছে নেবে, আগের SendGrid backend থাকলেও।

## ৩. Restart ও email যাচাই

1. Django backend বন্ধ করে আবার চালু করুন, যাতে নতুন `.env` পড়ে।
2. Register করুন বা verification page থেকে নতুন code resend করুন।
3. Brevo dashboard-এর **Transactional → Email → Logs**-এ status দেখুন; recipient-এর inbox, spam/junk-ও দেখুন। সফল API response `201` হয় এবং `messageId` দেয়।

`401` হলে API key ভুল/অকার্যকর হতে পারে; `403` হলে sender, account activation বা API key permission দেখুন। Free quota শেষ হলে Brevo dashboard-এ পরের দিনের reset পর্যন্ত অপেক্ষা করতে হবে। API error-এর response backend log-এ থাকবে, key value log হয় না।
