<script>
    let audioCtx, analyser, micStream;
    let sistemaConectado = false;
    let jarvisEncendido = false;
    let reconocedorVoz;
    let estaHablando = false;
    let ultimoPico = 0;

    async function iniciarSistema() {
        if (sistemaConectado) return;

        try {
            micStream = await navigator.mediaDevices.getUserMedia({ 
                audio: { 
                    echoCancellation: true, 
                    noiseSuppression: true, 
                    autoGainControl: true 
                } 
            });
            
            audioCtx = new (window.AudioContext || window.webkitAudioContext)();
            analyser = audioCtx.createAnalyser();
            
            const source = audioCtx.createMediaStreamSource(micStream);
            analyser.fftSize = 256;
            source.connect(analyser);

            sistemaConectado = true;
            document.getElementById('btnPower').style.display = 'none';
            document.getElementById('statusText').innerText = "EN ESPERA | DI 'JARVIS' O APLAUDE";
            document.getElementById('responseText').innerText = "Micrófono calibrado y listo...";

            iniciarSensorAplausos();
            iniciarReconocimientoVoz();
        } catch (err) {
            alert("Error al acceder al micrófono. Verifica los permisos del navegador.");
        }
    }

    // Detector de aplausos con umbral ajustado
    function iniciarSensorAplausos() {
        const bufferLength = analyser.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);

        function medir() {
            if (sistemaConectado && !jarvisEncendido && !estaHablando) {
                analyser.getByteFrequencyData(dataArray);
                let suma = 0;
                for (let i = 0; i < bufferLength; i++) suma += dataArray[i];
                let promedio = suma / bufferLength;

                // Bajamos el umbral de 85 a 60 para detectar aplausos más suaves
                if (promedio > 60) {
                    let ahora = Date.now();
                    if (ahora - ultimoPico < 600 && ahora - ultimoPico > 120) {
                        encenderJarvis();
                    }
                    ultimoPico = ahora;
                }
            }
            requestAnimationFrame(medir);
        }
        medir();
    }

    function encenderJarvis() {
        if (jarvisEncendido) return;
        jarvisEncendido = true;
        document.getElementById('orb').className = "orb";
        document.getElementById('statusText').innerText = "JARVIS ONLINE | TE ESCUCHO";
        hablar("A su servicio, señor. ¿Qué necesita?");
    }

    function apagarJarvis() {
        jarvisEncendido = false;
        document.getElementById('orb').className = "orb off";
        document.getElementById('statusText').innerText = "MODO ESPERA | DI 'JARVIS' O APLAUDE";
        document.getElementById('responseText').innerText = "Sistemas en reposo.";
    }

    function hablar(texto) {
        if ('speechSynthesis' in window) {
            window.speechSynthesis.cancel();
            const utt = new SpeechSynthesisUtterance(texto);
            utt.lang = 'es-ES';
            utt.rate = 1.0;
            utt.pitch = 0.8;

            utt.onstart = () => {
                estaHablando = true;
                if (reconocedorVoz) try { reconocedorVoz.stop(); } catch(e){}
                document.getElementById('orb').className = "orb speaking";
            };

            utt.onend = () => {
                estaHablando = false;
                if (jarvisEncendido) {
                    document.getElementById('orb').className = "orb";
                    document.getElementById('statusText').innerText = "JARVIS ONLINE | ESCUCHANDO";
                } else {
                    apagarJarvis();
                }
                reiniciarReconocimiento();
            };

            utt.onerror = () => {
                estaHablando = false;
                reiniciarReconocimiento();
            };

            window.speechSynthesis.speak(utt);
        }
    }

    function reiniciarReconocimiento() {
        if (sistemaConectado && reconocedorVoz) {
            setTimeout(() => {
                try { reconocedorVoz.start(); } catch(e){}
            }, 200);
        }
    }

    function iniciarReconocimientoVoz() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) {
            document.getElementById('responseText').innerText = "Navegador no compatible. Usa Google Chrome.";
            return;
        }

        reconocedorVoz = new SpeechRecognition();
        reconocedorVoz.continuous = true;
        reconocedorVoz.lang = 'es-ES';
        reconocedorVoz.interimResults = false;

        reconocedorVoz.onresult = async (event) => {
            if (estaHablando) return;

            const index = event.results.length - 1;
            let comando = event.results[index][0].transcript.trim().toLowerCase();

            // Eliminar tildes para simplificar la comparación
            comando = comando.normalize("NFD").replace(/[\u0300-\u036f]/g, "");
            console.log("Comando detectado:", comando);

            // 1. SI ESTÁ APAGADO: Buscar palabras clave de activación
            if (!jarvisEncendido) {
                if (comando.includes("jarvis") || comando.includes("hola") || comando.includes("despierta") || comando.includes("activate")) {
                    encenderJarvis();
                }
                return;
            }

            // 2. SI ESTÁ ENCENDIDO: Buscar palabras de apagado
            if (comando.includes("apagate") || comando.includes("descansa") || comando.includes("desactivate") || comando.includes("adios")) {
                hablar("Desactivando sistemas. Hasta luego, señor.");
                jarvisEncendido = false;
                return;
            }

            // 3. SI ESTÁ ENCENDIDO: Procesar pregunta
            document.getElementById('responseText').innerText = '"' + comando + '"';
            document.getElementById('orb').className = "orb listening";
            document.getElementById('statusText').innerText = "PROCESANDO...";

            try {
                const res = await fetch("/procesar", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ texto: comando })
                });
                const data = await res.json();
                
                document.getElementById('responseText').innerText = data.respuesta;
                hablar(data.respuesta);
            } catch (e) {
                document.getElementById('statusText').innerText = "ERROR DE CONEXIÓN";
                hablar("Error en el enlace de datos.");
            }
        };

        reconocedorVoz.onend = () => {
            if (!estaHablando && sistemaConectado) {
                reiniciarReconocimiento();
            }
        };

        try { reconocedorVoz.start(); } catch(e){}
    }
</script>
