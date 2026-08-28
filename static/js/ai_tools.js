/* Quanta AI: standalone frontend. No login or backend is included. */
const state = { documents: [], chats: [], activeChatId: null, page: 'assistant', apiKey: '', pendingAction: null, loading: false };
const $ = (selector) => document.querySelector(selector);
const pages = ['assistant', 'scamcheck', 'knowledge', 'documents', 'settings'];
const labels = { scamcheck: ['ScamCheck AI', 'Check an opportunity before you trust it'], knowledge: ['Knowledge Base', 'Upload and manage AI knowledge'], documents: ['Documents', 'View all available documents'], settings: ['Settings', 'Manage your application preferences'] };
const suggestions = ['What information is available in the knowledge base?', 'Summarize the uploaded documents', 'What are the important points?', 'Tell me about the available documents'];

function escapeHtml(value = '') { return String(value).replace(/[&<>'"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[c])); }
function formatBytes(bytes) { return `${(bytes / 1024 / 1024).toFixed(2)} MB`; }
function currentChat() { return state.chats.find(chat => chat.id === state.activeChatId); }
function readyDocs() { return state.documents.filter(doc => doc.status === 'ready'); }

function setPage(page) {
    state.page = page;
    pages.forEach(name => $(`#${name}Page`).hidden = name !== page);
    $('#chatInput').hidden = page !== 'assistant';
    $('#pageHeader').hidden = page === 'assistant';
    if (page !== 'assistant') { $('#pageTitle').textContent = labels[page][0]; $('#pageDescription').textContent = labels[page][1]; }
    document.querySelectorAll('.nav-link[data-page]').forEach(button => button.classList.toggle('active', button.dataset.page === page));
    $('#sidebar').classList.remove('open'); $('#overlay').classList.remove('visible');
    render();
}

function render() {
    const ready = readyDocs();
    $('#documentCount').textContent = state.documents.length || '';
    $('#documentCount').hidden = !state.documents.length;
    $('#readyPill').hidden = !ready.length;
    $('#readyPill').textContent = `${ready.length} document${ready.length === 1 ? '' : 's'} ready`;
    $('#questionInput').placeholder = ready.length ? 'Ask anything about your documents...' : 'Upload a document first...';
    $('#inputStatus').textContent = ready.length ? `${ready.length} document${ready.length === 1 ? '' : 's'} ready for AI search` : 'Upload a document to start building your knowledge base';
    renderHistory(); renderAssistant(); renderKnowledge(); renderDocuments();
}

function renderHistory() {
    const holder = $('#chatHistory');
    holder.innerHTML = state.chats.length ? state.chats.map(chat => `<button class="${chat.id === state.activeChatId ? 'active' : ''}" data-chat-id="${chat.id}">${escapeHtml(chat.title)}</button>`).join('') : '<p class="empty-note">No conversations yet</p>';
    holder.querySelectorAll('[data-chat-id]').forEach(button => button.onclick = () => { state.activeChatId = Number(button.dataset.chatId); setPage('assistant'); });
}

function renderAssistant() {
    const chat = currentChat(); const messages = chat?.messages || [];
    $('#emptyState').hidden = messages.length > 0; $('#messages').hidden = messages.length === 0;
    $('#suggestions').innerHTML = suggestions.map(question => `<button data-question="${escapeHtml(question)}">✦ ${escapeHtml(question)}</button>`).join('');
    $('#suggestions').querySelectorAll('button').forEach(button => button.onclick = () => sendMessage(button.dataset.question));
    $('#messages').innerHTML = messages.map(message => `<div class="message ${message.role}"><div class="bubble">${message.role === 'assistant' ? renderText(message.content) : escapeHtml(message.content)}${message.sources?.length ? `<div class="sources">${message.sources.map(source => `<span>▤ ${escapeHtml(source)}</span>`).join('')}</div>` : ''}</div></div>`).join('') + (state.loading ? '<div class="typing">Quanta AI is thinking…</div>' : '');
    if (messages.length) requestAnimationFrame(() => $('#messages').scrollTop = $('#messages').scrollHeight);
}
function renderText(text) { return escapeHtml(text).replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>').replace(/\n/g, '<br>'); }

function documentRows() {
    return state.documents.map(doc => `<div class="document-row"><span class="file-icon">▤</span><div><h3>${escapeHtml(doc.name)}</h3><p>${formatBytes(doc.size)}</p></div><span class="status">${doc.status === 'processing' ? 'Processing…' : doc.status === 'ready' ? '● Ready' : 'Unable to read'}</span><button title="Remove ${escapeHtml(doc.name)}" data-remove="${doc.id}">×</button></div>`).join('');
}
function bindRemoveButtons(root) { root.querySelectorAll('[data-remove]').forEach(button => button.onclick = () => { state.documents = state.documents.filter(doc => doc.id !== Number(button.dataset.remove)); render(); }); }
function renderKnowledge() { const holder = $('#knowledgeDocuments'); holder.innerHTML = state.documents.length ? `<div class="document-list"><h3>Uploaded documents (${state.documents.length})</h3>${documentRows()}</div>` : ''; bindRemoveButtons(holder); }
function renderDocuments() {
    const holder = $('#documentGrid');
    if (!state.documents.length) { holder.innerHTML = '<div class="empty-box">No documents uploaded yet<br><button id="goUpload">Upload documents</button></div>'; $('#goUpload').onclick = () => setPage('knowledge'); return; }
    holder.innerHTML = `<div class="doc-grid">${state.documents.map(doc => `<article class="doc-card"><span class="file-icon">▤</span><h3>${escapeHtml(doc.name)}</h3><p>Document · ${formatBytes(doc.size)}</p><div class="status">${doc.status === 'ready' ? '● Ready for AI search' : doc.status === 'processing' ? 'Processing document…' : 'Unable to extract text'}</div></article>`).join('')}</div>`;
}

function newChat() { state.activeChatId = null; $('#questionInput').value = ''; setPage('assistant'); }
function getOrCreateChat(question) {
    if (state.activeChatId) return currentChat();
    const chat = { id: Date.now(), title: question.length > 35 ? `${question.slice(0, 35)}…` : question, messages: [] };
    state.chats.unshift(chat); state.activeChatId = chat.id; return chat;
}
function addMessage(role, content, sources) { const chat = currentChat(); chat.messages.push({ role, content, sources }); render(); }

function searchDocuments(question) {
    const words = question.toLowerCase().match(/[a-z0-9]{3,}/g) || [];
    const chunks = readyDocs().flatMap(doc => {
        const parts = doc.text.match(/[\s\S]{1,1200}/g) || [];
        return parts.map(text => ({ name: doc.name, text, score: words.reduce((total, word) => total + ((text.toLowerCase().match(new RegExp(`\\b${word}\\b`, 'g')) || []).length), 0) }));
    }).filter(chunk => chunk.score > 0).sort((a, b) => b.score - a.score).slice(0, 6);
    const selected = chunks.length ? chunks : readyDocs().map(doc => ({ name: doc.name, text: doc.text.slice(0, 5000) }));
    return { context: selected.map((chunk, i) => `[Source ${i + 1}: ${chunk.name}]\n${chunk.text}`).join('\n\n---\n\n'), sources: [...new Set(selected.map(chunk => chunk.name))] };
}
async function sendMessage(preset) {
    const question = preset || $('#questionInput').value.trim(); if (!question || state.loading) return;
    getOrCreateChat(question); addMessage('user', question); $('#questionInput').value = '';
    if (!readyDocs().length) { addMessage('assistant', 'Please upload a document to the Knowledge Base before asking a question.'); return; }
    if (!state.apiKey) { addMessage('assistant', 'Add a Gemini API key in Settings to generate AI answers. Your documents are ready and local search is working.'); return; }
    state.loading = true; render();
    const { context, sources } = searchDocuments(question);
    try {
        const prompt = `You are Quanta AI. Answer only from the supplied document context. If the answer is missing, say: "I couldn't find that information in the uploaded documents." Be clear and concise.\n\nDOCUMENT CONTEXT:\n${context}\n\nUSER QUESTION:\n${question}`;
        const response = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent?key=${encodeURIComponent(state.apiKey)}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                contents: [{
                    parts: [{
                        text: prompt
                    }]
                }]
            })
        });
        const data = await response.json(); if (!response.ok) throw new Error(data?.error?.message || 'AI request failed');
        addMessage('assistant', data.candidates?.[0]?.content?.parts?.map(part => part.text).join('') || 'No answer was returned.', sources);
    } catch (error) { addMessage('assistant', `⚠️ ${error.message || 'Something went wrong while generating the answer. Please try again.'}`); }
    finally { state.loading = false; render(); }
}

async function extractText(file) {
    const name = file.name.toLowerCase();
    if (name.endsWith('.txt') || name.endsWith('.csv')) return file.text();
    if (name.endsWith('.pdf')) { const pdf = await pdfjsLib.getDocument({ data: new Uint8Array(await file.arrayBuffer()) }).promise; let result = ''; for (let i = 1; i <= pdf.numPages; i++) { const page = await pdf.getPage(i); result += (await page.getTextContent()).items.map(item => item.str || '').join(' ') + '\n\n'; } return result; }
    if (name.endsWith('.docx')) return (await mammoth.extractRawText({ arrayBuffer: await file.arrayBuffer() })).value;
    if (name.endsWith('.xlsx')) { const workbook = XLSX.read(await file.arrayBuffer(), { type: 'array' }); return workbook.SheetNames.map(sheet => `Sheet: ${sheet}\n${XLSX.utils.sheet_to_csv(workbook.Sheets[sheet])}`).join('\n\n'); }
    if (name.endsWith('.pptx')) { const zip = await JSZip.loadAsync(await file.arrayBuffer()); const names = Object.keys(zip.files).filter(path => /^ppt\/slides\/slide\d+\.xml$/.test(path)).sort((a, b) => Number(a.match(/\d+/)[0]) - Number(b.match(/\d+/)[0])); const slides = await Promise.all(names.map(async (name, index) => { const xml = await zip.files[name].async('text'); const text = [...xml.matchAll(/<a:t>(.*?)<\/a:t>/g)].map(match => match[1]).join(' '); return text ? `Slide ${index + 1}:\n${text}` : ''; })); return slides.filter(Boolean).join('\n\n'); }
    throw new Error('Unsupported file type');
}
async function uploadFiles(files) {
    for (const file of [...files]) { if (!/\.(pdf|txt|docx|csv|xlsx|pptx)$/i.test(file.name)) continue; const doc = { id: Date.now() + Math.random(), name: file.name, size: file.size, text: '', status: 'processing' }; state.documents.push(doc); render(); try { doc.text = await extractText(file); if (!doc.text.trim()) throw new Error('No readable text'); doc.status = 'ready'; } catch { doc.status = 'error'; } render(); }
}
function showConfirm(action) { state.pendingAction = action; $('#modalTitle').textContent = action === 'clearDocuments' ? 'Clear all documents?' : 'Clear current chat?'; $('#modalText').textContent = action === 'clearDocuments' ? 'All uploaded documents will be removed from the knowledge base.' : 'All messages in the current conversation will be removed.'; $('#modal').hidden = false; }

const scamExamples = {
    high: 'Congratulations! You have been selected for our internship program. Pay ₹1999 registration fee today. Only 10 seats remaining. Contact us on WhatsApp immediately.',
    medium: 'Exciting opportunity! Join our team as a Frontend Developer Intern. Work from home. Stipend ₹15,000/month. Contact: recruiter@gmail.com. Limited positions available. Apply today!',
    low: 'We are hiring Software Engineering Interns. Apply through our official careers page at careers.techcorp.com. The internship includes a technical interview and coding assessment. No payment is required. Location: Remote.'
};
const scamRules = [
    ['payment', /(registration|processing|training)\s*fee|pay\s*[₹\d,]+|security\s*deposit|payment\s*before\s*joining/i, 25, 'CRITICAL', '🔴', 'Payment request', 'This opportunity asks candidates to pay money.', 'Do not make any payment. Legitimate employers do not charge job or internship applicants.'],
    ['otp', /\botp\b|one[- ]time[- ]password|verification\s*code/i, 30, 'CRITICAL', '🔴', 'OTP request', 'The opportunity asks for OTP or verification codes.', 'Never share OTPs or verification codes.'],
    ['bank', /bank\s*(account|details|info)|account\s*number|\bifsc\b|\bupi\b|\bcvv\b|debit\s*card/i, 25, 'CRITICAL', '🔴', 'Banking information request', 'The opportunity asks for banking or payment details.', 'Do not share banking details until an employer is independently verified.'],
    ['selection', /guaranteed\s*(job|position|placement|selection)|100%\s*(placement|job)|congratulations.*selected|selected\s*for\s*(our\s*)?(internship|program|position)/i, 18, 'HIGH', '⚠️', 'False selection claim', 'It claims selection without a normal interview process.', 'Verify the hiring process through the company’s official website.'],
    ['urgency', /limited\s*(seats|positions|slots)|act\s*(now|immediately)|hurry\s*up|last\s*chance|only\s*\d+\s*(seats|spots|positions)|today\s*only/i, 15, 'HIGH', '⚠️', 'Urgency tactics', 'It uses pressure to make you act quickly.', 'Take time to verify the offer; legitimate employers do not rush candidates.'],
    ['email', /@(gmail|yahoo|outlook|hotmail|rediffmail)\.com/i, 10, 'MEDIUM', '📧', 'Personal email domain', 'The recruiter uses a personal email address.', 'Ask the employer to communicate through an official company domain.'],
    ['messaging', /whatsapp|telegram/i, 8, 'MEDIUM', '💬', 'Messaging-app communication', 'The offer relies on a messaging app.', 'Verify the recruiter and role through an official channel.'],
    ['url', /bit\.ly|tinyurl\.com|goo\.gl|ow\.ly|\b[a-z0-9-]+\.(xyz|click|top|club|online)\b/i, 8, 'MEDIUM', '🔗', 'Suspicious URL', 'The text contains a shortened or unusual URL.', 'Do not open the link until you verify its destination.']
];
const positiveRules = [
    [/careers\.[a-z0-9-]+\.(com|org|in)|apply\s*through\s*(our|the)\s*(website|portal|careers)/i, 8, 'Official careers page'],
    [/technical\s*(interview|round|assessment)|coding\s*(test|challenge|assessment)|interview\s*(process|round|schedule)/i, 5, 'Structured interview process'],
    [/responsibilities|requirements|qualifications|skills\s*(required|needed)|about\s*the\s*role/i, 5, 'Detailed job description'],
    [/no\s*(payment|fee|charges)\s*(required|needed|asked)?|free\s*internship/i, 10, 'No payment required']
];
function findEvidence(text, regex) { const match = text.match(regex); if (!match) return null; return text.slice(Math.max(0, match.index - 45), Math.min(text.length, match.index + match[0].length + 70)); }
function analyzeScam(text) {
    let score = 0, critical = 0; const indicators = []; const positives = [];
    scamRules.forEach(([, regex, weight, severity, icon, title, description, recommendation]) => { const evidence = findEvidence(text, regex); if (evidence) { score += weight; if (severity === 'CRITICAL') critical++; indicators.push({ severity, icon, title, description, recommendation, evidence }); } });
    positiveRules.forEach(([regex, weight, label]) => { if (regex.test(text)) { score -= weight; positives.push(label); } });
    if (critical) score = Math.floor(score * (1 + critical * .15)); score = Math.max(0, Math.min(100, score));
    const level = score <= 29 ? 'LOW' : score <= 59 ? 'MEDIUM' : score <= 79 ? 'HIGH' : 'CRITICAL';
    const checks = [['Company identity', '⚠️', 'Verify company registration'], ['Recruiter verification', '⚠️', 'Check recruiter credentials'], ['Payment security', '✅', 'No payment request detected'], ['Official application', '⚠️', 'Verify the application portal'], ['Interview process', '⚠️', 'Check the interview structure']];
    if (indicators.some(i => i.title === 'Payment request')) checks[2] = ['Payment security', '🔴', 'Payment requested — scam alert'];
    if (indicators.some(i => i.title === 'Personal email domain')) checks[1] = ['Recruiter verification', '🔴', 'Personal email used'];
    if (indicators.some(i => i.title === 'Urgency tactics' || i.title === 'Messaging-app communication')) checks[1] = ['Recruiter verification', '🔴', 'Contact needs careful verification'];
    if (positives.includes('Official careers page')) checks[3] = ['Official application', '✅', 'Official careers page mentioned'];
    if (positives.includes('Structured interview process')) checks[4] = ['Interview process', '✅', 'Interview process mentioned'];
    return { score, level, indicators, positives, checks };
}
function renderScamResult(result) {
    const color = result.level === 'CRITICAL' ? 'critical' : result.level === 'HIGH' ? 'high' : result.level === 'MEDIUM' ? 'medium' : 'low';
    $('#scamResult').hidden = false;
    $('#scamResult').innerHTML = `<article class="risk-summary ${color}"><div class="score-circle"><strong>${result.score}</strong><span>/100</span></div><div><b>${result.level} RISK</b><h2>${result.level === 'CRITICAL' ? 'Do not proceed' : result.level === 'HIGH' ? 'Proceed with extreme caution' : result.level === 'MEDIUM' ? 'Verify carefully' : 'Good signals detected'}</h2><p>${result.level === 'LOW' ? 'This looks safer based on the text, but you should still verify the employer independently.' : 'The analysis found warning signals. Do not share money, OTPs, banking details, or personal documents until the opportunity is verified.'}</p></div></article><div class="report-grid"><article class="report-card"><h3>Verification checklist</h3>${result.checks.map(c => `<div class="check-row"><span>${c[1]}</span><b>${c[0]}</b><small>${c[2]}</small></div>`).join('')}</article><article class="report-card"><h3>Warning indicators</h3>${result.indicators.length ? result.indicators.map(i => `<div class="indicator"><span>${i.icon}</span><div><b>${i.title}</b><small>${i.severity} · ${escapeHtml(i.description)}</small><em>“${escapeHtml(i.evidence)}”</em><p>💡 ${escapeHtml(i.recommendation)}</p></div></div>`).join('') : '<p class="no-risk">No high-risk patterns were detected in this text.</p>'}${result.positives.length ? `<p class="positive-signals">✓ ${result.positives.join(' · ')}</p>` : ''}</article></div>`;
}
function initializeScamCheck() {
    $('#scamText').oninput = event => $('#scamCharacterCount').textContent = `${event.target.value.length} / 10000 characters`;
    document.querySelectorAll('[data-scam-example]').forEach(button => button.onclick = () => { $('#scamText').value = scamExamples[button.dataset.scamExample]; $('#scamText').dispatchEvent(new Event('input')); });
    document.querySelectorAll('[data-scam-tab]').forEach(button => button.onclick = () => { const image = button.dataset.scamTab === 'image'; document.querySelectorAll('[data-scam-tab]').forEach(tab => tab.classList.toggle('active', tab === button)); $('#scamTextPane').hidden = image; $('#scamImagePane').hidden = !image; });
    $('#scamUploadButton').onclick = () => $('#scamImageInput').click(); $('#scamImageInput').onchange = event => { const file = event.target.files[0]; if (!file) return; if (!/^image\/(png|jpeg|webp)$/.test(file.type) || file.size > 5 * 1024 * 1024) { $('#scamOcrNote').textContent = 'Please select a PNG, JPG, or WEBP image under 5 MB.'; return; } const reader = new FileReader(); reader.onload = () => { $('#scamImagePreview').src = reader.result; $('#scamImagePreview').hidden = false; $('#scamOcrNote').textContent = 'Screenshot loaded. Paste the visible offer text in the Paste text tab to analyze it.'; }; reader.readAsDataURL(file); };
    $('#analyzeScamButton').onclick = () => { const text = $('#scamText').value.trim(); if (text.length < 10) { $('#scamOcrNote').textContent = 'Paste at least 10 characters of offer text before analysis.'; return; } renderScamResult(analyzeScam(text)); $('#scamResult').scrollIntoView({ behavior: 'smooth', block: 'start' }); };
}

document.addEventListener('DOMContentLoaded', () => {
    $('#suggestions').innerHTML = '';
    document.querySelectorAll('[data-page]').forEach(button => button.onclick = () => setPage(button.dataset.page));
    $('#newChat').onclick = newChat; $('#menuButton').onclick = () => { $('#sidebar').classList.add('open'); $('#overlay').classList.add('visible'); }; $('#overlay').onclick = () => { $('#sidebar').classList.remove('open'); $('#overlay').classList.remove('visible'); };
    $('#uploadZone').onclick = () => $('#fileInput').click(); $('#fileInput').onchange = event => uploadFiles(event.target.files);
    $('#sendButton').onclick = () => sendMessage(); $('#questionInput').onkeydown = event => { if (event.key === 'Enter') sendMessage(); };
    $('#saveKey').onclick = () => { state.apiKey = $('#apiKeyInput').value.trim(); $('#apiKeyInput').value = ''; $('#saveKey').textContent = state.apiKey ? 'Saved' : 'Save'; setTimeout(() => $('#saveKey').textContent = 'Save', 1000); };
    document.querySelectorAll('[data-confirm]').forEach(button => button.onclick = () => showConfirm(button.dataset.confirm));
    $('#cancelModal').onclick = () => $('#modal').hidden = true; $('#confirmModal').onclick = () => { if (state.pendingAction === 'clearDocuments') state.documents = []; else if (currentChat()) currentChat().messages = []; $('#modal').hidden = true; render(); };
    initializeScamCheck();
    render();
});