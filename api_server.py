@app.get("/verify-ad/{token}", response_class=HTMLResponse)
async def verify_ad_page(token: str):
    """
    صفحة HTML لمشاهدة الإعلان مع مؤقت إجباري (15 ثانية)
    """
    # التحقق من وجود التوكن (المنطق الأصلي)
    token_data = get_token_data(token)
    
    if not token_data:
        return """
        <!DOCTYPE html>
        <html dir="rtl">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>خطأ</title>
        </head>
        <body style="font-family: Arial; text-align: center; padding: 50px;">
            <h1>❌ رابط غير صالح</h1>
            <p>الرابط الذي استخدمته غير صحيح أو منتهي الصلاحية.</p>
        </body>
        </html>
        """
    
    if token_data["verified"]:
        return """
        <!DOCTYPE html>
        <html dir="rtl">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>تم التحقق</title>
        </head>
        <body style="font-family: Arial; text-align: center; padding: 50px;">
            <h1>✅ تم التحقق مسبقاً</h1>
            <p>لقد تم التحقق من هذا الإعلان مسبقاً.</p>
            <p>يمكنك العودة للبوت.</p>
        </body>
        </html>
        """
    
    # صفحة المشاهدة المعدلة مع التايمر
    REQUIRED_VIEW_TIME = 15 # ثابت للعرض في الكود (محدد بـ 15 ثانية)
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>مشاهدة الإعلان - بوت منهج AI</title>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
                padding: 20px;
            }}
            .container {{
                background: white;
                border-radius: 20px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                max-width: 600px;
                width: 100%;
                padding: 40px;
                text-align: center;
            }}
            h1 {{
                color: #667eea;
                margin-bottom: 20px;
            }}
            /* نمط رسالة الحالة الرئيسية */
            #mainStatus {{
                font-size: 18px;
                font-weight: bold;
                color: #764ba2;
                margin-bottom: 15px;
                padding: 10px;
                border-radius: 8px;
                background-color: #f7f7ff;
            }}
            .status-done {{
                color: #27ae60 !important;
                background-color: #e6ffe6;
            }}
            .instructions {{
                background: #fff3cd;
                border: 2px solid #ffeaa7;
                border-radius: 10px;
                padding: 20px;
                margin: 20px 0;
                text-align: right;
            }}
            .instructions ol {{
                margin-right: 20px;
            }}
            .instructions li {{
                margin: 10px 0;
                font-size: 16px;
            }}
            .ad-link {{
                display: inline-block;
                background: #3498db;
                color: white;
                padding: 15px 30px;
                text-decoration: none;
                border-radius: 10px;
                font-size: 18px;
                font-weight: bold;
                margin: 20px 0;
                transition: all 0.3s;
            }}
            .ad-link:hover {{
                background: #2980b9;
                transform: translateY(-2px);
            }}
            #confirmBtn {{
                background: #27ae60;
                color: white;
                border: none;
                padding: 18px 40px;
                font-size: 20px;
                font-weight: bold;
                border-radius: 50px;
                cursor: pointer;
                transition: all 0.3s;
                margin-top: 20px;
            }}
            #confirmBtn:hover:not(:disabled) {{
                background: #229954;
                transform: translateY(-2px);
            }}
            #confirmBtn:disabled {{
                background: #95a5a6; /* لون رمادي لزر معطل */
                cursor: not-allowed;
                transform: none;
            }}
            #message {{
                margin-top: 20px;
                padding: 15px;
                border-radius: 10px;
                display: none;
            }}
            .success {{
                background: #d4edda;
                color: #155724;
                border: 2px solid #c3e6cb;
            }}
            .error {{
                background: #f8d7da;
                color: #721c24;
                border: 2px solid #f5c6cb;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎯 شاهد الإعلان للحصول على النقاط</h1>
            
            <p id="mainStatus">
                1. اضغط على زر "🌐 فتح الإعلان" لبدء المشاهدة والمؤقت.
            </p>

            <div class="instructions">
                <strong>📋 التعليمات:</strong>
                <ol>
                    <li>اضغط على زر "فتح الإعلان" أدناه <b>(لبدء المؤقت)</b></li>
                    <li>ابقَ في صفحة الإعلان حتى انتهاء المؤقت <b>({REQUIRED_VIEW_TIME} ثانية)</b></li>
                    <li>ارجع لهذه الصفحة واضغط على زر "أكد المشاهدة" (سيتم تفعيله بعد انتهاء المؤقت)</li>
                </ol>
            </div>
            
            <a href="{AD_LINK}" target="_blank" class="ad-link" onclick="startVerification()">
                🌐 فتح الإعلان
            </a>
            
            <br><br>
            
            <button id="confirmBtn" onclick="confirmView()" disabled>
                ⏳ انتظر {REQUIRED_VIEW_TIME} ثانية...
            </button>
            
            <div id="message"></div>
        </div>

        <script>
            const token = '{token}';
            const REQUIRED_VIEW_TIME = 15; // 15 ثانية للمشاهدة
            
            let timeLeft = REQUIRED_VIEW_TIME;
            let timerInterval = null;
            let timerStarted = false;
            
            const confirmBtn = document.getElementById('confirmBtn');
            const mainStatus = document.getElementById('mainStatus');
            const msgDiv = document.getElementById('message');

            function updateTimerDisplay() {{
                if (timeLeft > 0) {{
                    confirmBtn.textContent = `⏳ انتظر ${timeLeft} ثانية...`;
                    mainStatus.innerHTML = `2. الرجاء البقاء في الإعلان! المتبقي: <b>${timeLeft} ثانية</b> ⏳`;
                }} else {{
                    clearInterval(timerInterval);
                    confirmBtn.textContent = '✅ أكد المشاهدة الآن';
                    confirmBtn.disabled = false;
                    mainStatus.innerHTML = '✅ <b>انتهى وقت المشاهدة!</b> اضغط "أكد المشاهدة"';
                    mainStatus.classList.add('status-done');
                }}
            }}
            
            function startTimer() {{
                if (timerStarted) return;
                
                timerStarted = true;
                confirmBtn.disabled = true;
                
                updateTimerDisplay();
                
                timerInterval = setInterval(() => {{
                    timeLeft--;
                    updateTimerDisplay();
                    
                    if (timeLeft <= 0) {{
                        clearInterval(timerInterval);
                    }}
                }}, 1000);
            }}

            function startVerification() {{
                // إذا حاول الفتح مرة أخرى والمؤقت يعمل
                if (timerStarted && timeLeft > 0) {{
                     mainStatus.innerHTML = `2. المؤقت قيد التشغيل: <b>${timeLeft} ثانية</b> متبقية.`;
                     return;
                }}

                // إذا حاول الفتح بعد الانتهاء
                if (timeLeft <= 0) {{
                     mainStatus.innerHTML = '✅ <b>انتهى وقت المشاهدة!</b> اضغط "أكد المشاهدة"';
                     return;
                }}

                // عند الضغط لأول مرة
                startTimer();
                msgDiv.style.display = 'none'; // إخفاء أي رسالة سابقة
            }}
            
            async function confirmView() {{
                // الشرط الحاسم: التحقق من انتهاء المؤقت وبدئه
                if (timeLeft > 0 || !timerStarted) {{
                    msgDiv.className = 'error';
                    msgDiv.style.display = 'block';
                    msgDiv.innerHTML = '⚠️ يجب عليك الانتظار حتى انتهاء العداد بعد الضغط على "فتح الإعلان"!';
                    return;
                }}
                
                // بدء عملية التحقق (API Call)
                confirmBtn.disabled = true;
                confirmBtn.textContent = '⏳ جاري التحقق...';
                msgDiv.style.display = 'none';
                
                try {{
                    // هنا يتم استدعاء API /api/complete-ad
                    const response = await fetch('/api/complete-ad', {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/json'
                        }},
                        body: JSON.stringify({{ token: token }})
                    }});
                    
                    const data = await response.json();
                    
                    if (data.success) {{
                        msgDiv.className = 'success';
                        msgDiv.innerHTML = 
                            '✅ <strong>تم التحقق بنجاح!</strong><br><br>' +
                            '🎁 سيتم إضافة النقاط لحسابك خلال ثوانٍ<br>' +
                            '🔙 يمكنك العودة للبوت الآن';
                        mainStatus.style.display = 'none'; // إخفاء حالة المشاهدة بعد النجاح
                        confirmBtn.style.display = 'none'; // إخفاء الزر بعد النجاح
                    }} else {{
                        msgDiv.className = 'error';
                        msgDiv.innerHTML = '❌ <strong>حدث خطأ:</strong><br>' + (data.error || 'خطأ غير معروف');
                        confirmBtn.disabled = false;
                        confirmBtn.textContent = '✅ أكد المشاهدة الآن'; // إعادة الزر لحالته
                    }}
                    msgDiv.style.display = 'block';
                }} catch (error) {{
                    // هذا هو الجزء الذي يعالج خطأ الاتصال (No Internet)
                    msgDiv.className = 'error';
                    msgDiv.innerHTML = '❌ <strong>خطأ في الاتصال</strong><br>يرجى المحاولة مرة أخرى والتأكد من اتصالك بالإنترنت.';
                    msgDiv.style.display = 'block';
                    confirmBtn.disabled = false;
                    confirmBtn.textContent = '✅ أكد المشاهدة الآن'; // إعادة الزر لحالته
                }}
            }}

            // عند تحميل الصفحة
            updateTimerDisplay();

        </script>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html_content)
