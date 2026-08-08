# StarLink Bot Deployment

ဒီ Bot ကို Render.com မှာ အလွယ်ကူဆုံး Deploy လုပ်ဖို့ အောက်ပါခလုတ်ကို နှိပ်ပါ။

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/thetpaingzaw130-ai/starlink-bot-deploy)

## အသုံးပြုနည်း (အဆင့်ဆင့်)

### ၁။ Render မှာ အကောင့်ဖွင့်ပါ
[Render.com](https://render.com/) ကိုသွားပြီး GitHub အကောင့်နဲ့ Login ဝင်လိုက်ပါ။

### ၂။ Deploy လုပ်ပါ
အပေါ်က **"Deploy to Render"** ခလုတ်ကို နှိပ်ပါ။ ပြီးရင် ပေါ်လာတဲ့စာမျက်နှာမှာ ဘာမှပြင်စရာမလိုဘဲ အောက်ဆုံးက **"Create Web Service"** ကို နှိပ်လိုက်ပါ။

### ၃။ ၂၄ နာရီ အလုပ်လုပ်အောင် လုပ်နည်း
Render Free Tier က လူမသုံးရင် ခဏနားသွားတတ်ပါတယ်။ အမြဲအလုပ်လုပ်နေအောင် အောက်ပါအတိုင်း လုပ်ပေးပါ-
1. [UptimeRobot](https://uptimerobot.com/) မှာ အကောင့်ဖွင့်ပါ။
2. **"Add New Monitor"** ကိုနှိပ်ပါ။
3. **Monitor Type:** `HTTP(s)` ကိုရွေးပါ။
4. **Friendly Name:** `Starlink Bot` လို့ပေးပါ။
5. **URL:** နေရာမှာ Render ကပေးတဲ့ သင်၏ App URL (ဥပမာ- `https://starlink-bot-xxxx.onrender.com/`) ကို ထည့်ပါ။
6. **Monitoring Interval:** `5 minutes` ထားပြီး **Create Monitor** ကို နှိပ်ပါ။

ဒါဆိုရင် သင်၏ Bot သည် ၂၄ နာရီပတ်လုံး အခမဲ့ အလုပ်လုပ်နေပါလိမ့်မယ်။
