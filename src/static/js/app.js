// ---- Config ----
const API_BASE_URL = window.location.origin + '/api/v1';

// ---- State ----
let conversations = [];
let activeConvId = null;
let isProcessing = false;
const STORAGE_KEY = 'vimedbot_state';

// ---- Elements ----
const convList = document.getElementById('convList');
const emptyHint = document.getElementById('emptyHint');
const messagesEl = document.getElementById('messages');
const inputBox = document.getElementById('inputBox');
const btnSend = document.getElementById('btnSend');
const btnNewChat = document.getElementById('btnNewChat');
const btnToggleSidebar = document.getElementById('btnToggleSidebar');
const leftSidebar = document.getElementById('leftSidebar');
const btnInfo = document.getElementById('btnInfo');
const infoModal = document.getElementById('infoModal');

// ---- Storage ----
function loadState() {
  const data = localStorage.getItem(STORAGE_KEY);
  if (data) {
    const parsed = JSON.parse(data);
    conversations = parsed.conversations || [];
    activeConvId = parsed.activeConvId;
    if (conversations.length > 0 && !activeConvId) {
      activeConvId = conversations[0].id;
    }
  }
}

function saveState() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify({
    conversations,
    activeConvId
  }));
}

// ---- Markdown-lite -> Safe HTML (no external libs) ----
function escapeHTML(s) {
  return s.replace(/[&<>"']/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
}

function linkify(s) {
  return s.replace(/\bhttps?:\/\/[^\s)]+/g, url => `<a href="${url}" target="_blank" rel="noopener noreferrer">${url}</a>`);
}

function renderMarkdownLite(md) {
  if (!md) return "";

  // Chuẩn hóa bullets
  const normalizeRawBullets = (s) => {
    s = s.replace(/([:.;])\s*\*\s+/g, (_, p1) => `${p1}\n- `);
    s = s.replace(/^\s*\*\s+/gm, '- ');
    s = s.replace(/\s+\*\s+/g, '\n- ');
    return s;
  };

  // An toàn trước
  let txt = escapeHTML(normalizeRawBullets(md.trim()));

  // Xử lý code blocks và inline code
  txt = txt.replace(/```([\s\S]*?)```/g, (_, code) => `<pre class="codeblock"><code>${escapeHTML(code)}</code></pre>`);
  txt = txt.replace(/`([^`]+)`/g, (_, code) => `<code class="code-inline">${escapeHTML(code)}</code>`);
  txt = txt.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
  txt = txt.replace(/\*([^*\n]+)\*/g, '<em>$1</em>');
  txt = linkify(txt);

  // Parse danh sách lồng nhau
  const lines = txt.split(/\r?\n/);
  let html = '';
  let stack = [{ level: 0, html: '', isOL: false }]; // Stack để quản lý cấp độ và loại danh sách

  const closeLists = (upToLevel) => {
    while (stack.length > 1 && stack[stack.length - 1].level >= upToLevel) {
      const top = stack.pop();
      stack[stack.length - 1].html += top.html + (top.isOL ? '</ol>' : '</ul>');
    }
  };

  for (let i = 0; i < lines.length; i++) {
    let line = lines[i].trim();
    if (!line) { 
      closeLists(0);
      stack[stack.length - 1].html += '<br/>'; 
      continue; 
    }

    // Kiểm tra mức độ thụt đầu dòng
    const indentMatch = lines[i].match(/^(\s*)/);
    const indentLevel = indentMatch[0].length / 2; // Mỗi 2 khoảng trắng = 1 cấp
    const ulMatch = line.match(/^[-*•]\s+(.+)$/);
    const olMatch = line.match(/^\d+\.\s+(.+)$/);

    if (ulMatch || olMatch) {
      const content = ulMatch ? ulMatch[1] : olMatch[1];
      const isOL = !!olMatch;
      const currentLevel = indentLevel + 1;

      // Đóng các danh sách ở cấp cao hơn hoặc bằng
      closeLists(currentLevel);

      // Nếu cấp hiện tại cao hơn stack, mở danh sách mới
      if (currentLevel > stack[stack.length - 1].level) {
        stack.push({ level: currentLevel, html: isOL ? '<ol>' : '<ul>', isOL });
      } else if (currentLevel === stack[stack.length - 1].level && stack[stack.length - 1].isOL !== isOL) {
        // Chuyển từ UL sang OL hoặc ngược lại ở cùng cấp
        const top = stack.pop();
        stack[stack.length - 1].html += top.html + (top.isOL ? '</ol>' : '</ul>');
        stack.push({ level: currentLevel, html: isOL ? '<ol>' : '<ul>', isOL });
      }

      // Thêm mục danh sách
      stack[stack.length - 1].html += `<li>${content}</li>`;
    } else {
      // Không phải danh sách, đóng tất cả danh sách và thêm paragraph
      closeLists(0);
      stack[0].html += `<p>${line}</p>`;
    }
  }

  // Đóng tất cả danh sách còn lại
  closeLists(0);
  html = stack[0].html;

  return `<div class="ai-answer">${html}</div>`;
}

// ---- Utils ----
const nowLabel = () => {
  const now = new Date();
  const hours = now.getHours().toString().padStart(2, '0');
  const minutes = now.getMinutes().toString().padStart(2, '0');
  return `${hours}:${minutes}`;
};
const gid = () => Math.floor(Math.random()*1e9).toString();

// ---- API Calls ----
async function callChatAPI(message, conversationId) {
  const response = await fetch(`${API_BASE_URL}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message: message,
      conversation_id: conversationId,
      use_query_expansion: true,
      top_k: 12,
      rerank_top_n: 5
    })
  });
  if (!response.ok) {
    throw new Error(`API Error: ${response.status}`);
  }
  return await response.json();
}

// ---- Render Functions ----
function renderConversations() {
  convList.innerHTML = '';
  if (conversations.length === 0) {
    convList.appendChild(emptyHint);
    emptyHint.style.display = 'block';
    return;
  }
  emptyHint.style.display = 'none';

  conversations.forEach(c => {
    const item = document.createElement('div');
    item.className = 'conv' + (c.id === activeConvId ? ' active' : '');
    item.dataset.id = c.id;

    const icon = document.createElement('i');
    icon.setAttribute('data-lucide', 'message-square');
    icon.className = 'conv__icon';

    const meta = document.createElement('div');
    meta.className = 'conv__meta';

    const titleWrap = document.createElement('div');
    if (c.editing) {
      const input = document.createElement('input');
      input.className = 'conv__edit';
      input.value = c.title;
      input.placeholder = 'Nhập tên cuộc trò chuyện';
      input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
          const v = input.value.trim();
          if (v) { c.title = v; }
          c.editing = false;
          renderConversations();
          saveState();
        } else if (e.key === 'Escape') {
          c.editing = false;
          renderConversations();
          saveState();
        }
      });
      input.addEventListener('blur', () => {
        const v = input.value.trim();
        if (v) { c.title = v; }
        c.editing = false;
        renderConversations();
        saveState();
      });
      setTimeout(() => { input.focus(); input.select(); }, 0);
      titleWrap.appendChild(input);
    } else {
      const title = document.createElement('div');
      title.className = 'conv__title';
      title.textContent = c.title;
      titleWrap.appendChild(title);
    }

    const date = document.createElement('div');
    date.className = 'conv__date';
    date.textContent = c.date;

    meta.appendChild(titleWrap);
    meta.appendChild(date);

    const actions = document.createElement('div');
    actions.className = 'conv__actions';

    const btnRename = document.createElement('button');
    btnRename.className = 'icon-btn icon-btn--xs';
    btnRename.title = 'Đổi tên';
    const icRen = document.createElement('i');
    icRen.setAttribute('data-lucide', 'pencil');
    btnRename.appendChild(icRen);
    btnRename.addEventListener('click', (e) => {
      e.stopPropagation();
      c.editing = true;
      renderConversations();
    });

    const btnDel = document.createElement('button');
    btnDel.className = 'icon-btn icon-btn--xs';
    btnDel.title = 'Xóa';
    const icDel = document.createElement('i');
    icDel.setAttribute('data-lucide', 'trash-2');
    btnDel.appendChild(icDel);
    btnDel.addEventListener('click', (e) => {
      e.stopPropagation();
      if (confirm('Bạn có chắc muốn xóa cuộc trò chuyện này?')) {
        conversations = conversations.filter(x => x.id !== c.id);
        if (activeConvId === c.id) {
          activeConvId = conversations[0]?.id ?? null;
        }
        renderConversations();
        renderMessages();
        saveState();
      }
    });

    actions.appendChild(btnRename);
    actions.appendChild(btnDel);

    item.addEventListener('click', () => {
      if (!c.editing) {
        activeConvId = c.id;
        renderConversations();
        renderMessages();
        saveState();
      }
    });

    item.appendChild(icon);
    item.appendChild(meta);
    item.appendChild(actions);
    convList.appendChild(item);
  });

  lucide.createIcons();
}

function renderMessages() {
  messagesEl.innerHTML = '';
  const conv = conversations.find(c => c.id === activeConvId);
  if (!conv) return;

  conv.messages.forEach(m => {
    const row = document.createElement('div');
    row.className = 'msg ' + (m.role === 'user' ? 'msg--right' : 'msg--left') + ' msg--' + m.role;

    if (m.role === 'assistant') {
      const av = document.createElement('div');
      av.className = 'avatar';
      av.textContent = 'VM';
      row.appendChild(av);
    }

    const bubble = document.createElement('div');
    bubble.className = 'msg__bubble';

    if (m.isLoading) {
      bubble.innerHTML = '<div class="typing-indicator"><span></span><span></span><span></span></div>';
    } else {
      bubble.innerHTML = m.role === 'assistant' ? renderMarkdownLite(m.content) : escapeHTML(m.content);
    }

    row.appendChild(bubble);

    if (m.role === 'user') {
      const avU = document.createElement('div');
      avU.className = 'avatar avatar--user';
      const userI = document.createElement('i');
      userI.setAttribute('data-lucide', 'user');
      avU.appendChild(userI);
      row.appendChild(avU);
    }

    messagesEl.appendChild(row);
  });

  messagesEl.scrollTop = messagesEl.scrollHeight;
  lucide.createIcons();
}

// ---- Actions ----
function ensureActiveConv() {
  if (activeConvId) return;
  const id = gid();
  conversations.unshift({
    id,
    title: 'Cuộc trò chuyện mới',
    date: nowLabel(),
    messages: [{
      id: gid(),
      role: 'assistant',
      content: 'Xin chào! Tôi là ViMedBot - trợ lý AI về sức khỏe. Tôi có thể giúp gì cho bạn hôm nay?'
    }]
  });
  activeConvId = id;
  renderConversations();
  saveState();
}

async function sendMessage() {
  const text = inputBox.value.trim();
  if (!text || isProcessing) return;

  ensureActiveConv();
  const conv = conversations.find(c => c.id === activeConvId);

  // Add user message
  conv.date = nowLabel();
  conv.messages.push({ id: gid(), role: 'user', content: text });
  inputBox.value = '';
  isProcessing = true;
  btnSend.disabled = true;
  inputBox.disabled = true;

  // Loading message
  const loadingId = gid();
  conv.messages.push({ id: loadingId, role: 'assistant', isLoading: true });

  renderConversations();
  renderMessages();

  try {
    const response = await callChatAPI(text, conv.id);

    // Remove loading
    conv.messages = conv.messages.filter(m => m.id !== loadingId);

    // Add real response (frontend will format)
    const content = response.answer_html ?? response.answer ?? '';
    conv.messages.push({ id: gid(), role: 'assistant', content });

    // Auto title
    if (conv.title === 'Cuộc trò chuyện mới' && conv.messages.length <= 4) {
      conv.title = text.length > 40 ? text.substring(0, 40) + '...' : text;
    }

  } catch (error) {
    conv.messages = conv.messages.filter(m => m.id !== loadingId);
    conv.messages.push({
      id: gid(),
      role: 'assistant',
      content: 'Xin lỗi, có lỗi xảy ra khi xử lý câu hỏi của bạn. Vui lòng thử lại sau.'
    });
    console.error('API Error:', error);
  } finally {
    isProcessing = false;
    btnSend.disabled = false;
    inputBox.disabled = false;
    inputBox.focus();
    renderConversations();
    renderMessages();
    saveState();
  }
}

// ---- Events ----
btnNewChat.addEventListener('click', () => {
  const id = gid();
  conversations.unshift({
    id,
    title: 'Cuộc trò chuyện mới',
    date: nowLabel(),
    messages: [{
      id: gid(),
      role: 'assistant',
      content: 'Xin chào! Tôi là ViMedBot - trợ lý AI về sức khỏe. Tôi có thể giúp gì cho bạn hôm nay?'
    }]
  });
  activeConvId = id;
  renderConversations();
  renderMessages();
  saveState();
  inputBox.focus();
});

btnSend.addEventListener('click', sendMessage);
inputBox.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

btnToggleSidebar.addEventListener('click', () => {
  leftSidebar.classList.toggle('sidebar--collapsed');
});

btnInfo.addEventListener('click', () => infoModal.classList.add('show'));
infoModal.addEventListener('click', (e) => {
  if (e.target.dataset.close === 'modal' || e.target.closest('[data-close="modal"]')) {
    infoModal.classList.remove('show');
  }
});

// ---- Init ----
loadState();
if (conversations.length === 0) {
  const id = gid();
  conversations.unshift({
    id,
    title: 'Cuộc trò chuyện mới',
    date: nowLabel(),
    messages: [{
      id: gid(),
      role: 'assistant',
      content: 'Xin chào! Tôi là ViMedBot - trợ lý AI về sức khỏe. Tôi có thể giúp gì cho bạn hôm nay?'
    }]
  });
  activeConvId = id;
  saveState();
}
renderConversations();
renderMessages();
inputBox.focus();

lucide.createIcons();