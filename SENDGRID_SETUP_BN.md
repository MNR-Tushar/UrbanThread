# UrbanThread-এ SendGrid email verification setup

এই প্রজেক্টে signup-এর পর ৬ সংখ্যার OTP ইমেইলে পাঠানোর flow আগে থেকেই আছে। SendGrid-এর HTTPS Mail Send API ব্যবহার করলে signup verification, resend verification, password reset এবং welcome email একই sender দিয়ে যাবে। OTP ১৫ মিনিটে মেয়াদোত্তীর্ণ হয়। HTTPS API ব্যবহার করায় SMTP port খোলা থাকা লাগে না।

## ১. SendGrid account ও sender তৈরি করুন

1. [SendGrid](https://signup.sendgrid.com/) account তৈরি করে account verification শেষ করুন। SendGrid account approval বা sending limits থাকলে সেগুলোও সম্পন্ন করুন।
2. পরীক্ষার জন্য SendGrid Console-এ **Settings → Sender Authentication → Verify a Single Sender** খুলে যে mailbox-টি আপনার, সেটি verify করুন। Free account-এ sender verify করা আবশ্যক। Production-এ আপনার নিজস্ব domain থাকলে **Domain Authentication** সেট করুন; DNS-এ SendGrid যে records দেখায় সেগুলো আপনার DNS provider-এ যোগ করুন।
3. **Settings → API Keys → Create API Key** থেকে API key তৈরি করুন, যাতে **Mail Send** permission থাকে। Key-টি তৈরির সময়ই কপি করে নিরাপদে রাখুন; পরে সম্পূর্ণ key আবার দেখা নাও যেতে পারে।

API key আপনার SendGrid account password নয়। এই backend HTTPS `Authorization: Bearer` header-এ API key পাঠায়।

## ২. Backend-এর `.env` সেট করুন

`urbanthread/.env`-এ নিচের মানগুলো যোগ/আপডেট করুন। `DEFAULT_FROM_EMAIL` অবশ্যই SendGrid-এ verified sender-এর email-এর সঙ্গে মিলতে হবে।

```dotenv
SENDGRID_API_KEY=SG.your-real-api-key
DEFAULT_FROM_EMAIL=verified-sender@your-domain.com

# Optional: defaults shown here
EMAIL_BACKEND=accounts.email_backend.SendGridEmailBackend
SENDGRID_API_URL=https://api.sendgrid.com/v3/mail/send
SENDGRID_API_TIMEOUT=15
```

`SENDGRID_API_KEY`-কে Git-এ commit করবেন না; `.env` ইতিমধ্যে `.gitignore` করা আছে। Hosting provider-এ deploy করলে একই নামের environment variables সেখানে secret হিসেবে সেট করুন। Docker Compose-এ `web`, `celery`, এবং `celery_beat` services `.env` থেকে environment পড়ে, তাই আলাদা করে compose file সম্পাদনা করতে হবে না।

`EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, এবং `EMAIL_HOST_PASSWORD` এই backend-এ ব্যবহার হয় না।

## ৩. চালু ও যাচাই করুন

1. Development server চালু/পুনরায় চালু করুন। Docker হলে `docker compose up -d --build` চালান; সাধারণ local run হলে backend server restart করুন।
2. Frontend থেকে নতুন customer account register করে inbox এবং spam/junk folder দেখুন। ৬ সংখ্যার verification code পাঠানো উচিত।
3. Code দিয়ে verify করুন। Signup response-এ `verification_required: true` আসে; verification সফল হলে frontend login token পায়। Resend, password reset এবং welcome email-ও একই SendGrid HTTPS configuration ব্যবহার করে।

Email না এলে backend log-এর SendGrid HTTP status ও response দেখুন। `401` হলে API key যাচাই করুন; `403` হলে key-এর Mail Send permission এবং sender verification পরীক্ষা করুন। `202` মানে SendGrid email গ্রহণ করেছে; এরপর SendGrid Email Activity ও inbox-এর spam/junk folder দেখুন। API key কখনো log বা chat-এ শেয়ার করবেন না।

## ৪. API endpoint

- `POST /accounts/register/` — account তৈরি করে verification code পাঠায়।
- `POST /accounts/email/verification/confirm/` — email এবং ছয় সংখ্যার OTP দিয়ে account verify করে।
- `POST /accounts/email/verification/resend/` — নতুন OTP পাঠায়।

SendGrid-এর official API নির্দেশনা: [Mail Send API](https://www.twilio.com/docs/sendgrid/api-reference/mail-send/mail-send)। Sender verification: [Single Sender Verification](https://www.twilio.com/docs/sendgrid/ui/sending-email/sender-verification), [Sender Identity](https://www.twilio.com/docs/sendgrid/for-developers/sending-email/sender-identity)।
