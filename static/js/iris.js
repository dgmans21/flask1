/**
 * AI Studio — iris.js
 * 모델별 오버레이 열기 / API 제출 / 결과 표시
 */

const MODELS = {
  iris: {
    id: 'iris',
    label: 'Iris 붓꽃 분류',
    type: 'classification',
    overlayId: 'overlay-iris',
    formId: 'form-iris',
    resultId: 'result-iris',
    valueId: 'result-iris-value',
    messageId: 'result-iris-message',
    submitBtnId: 'btn-iris-submit',
    api: '/api/ai/predict_iris',
    fields: ['sepal_length', 'sepal_width', 'petal_length', 'petal_width'],
    defaults: { sepal_length: 5.8, sepal_width: 3.0, petal_length: 3.8, petal_width: 1.2 },
    submitLabel: '예측 실행',
    loadingLabel: '예측 중…',
    formatResult(data) {
      return data?.result ?? '—';
    },
    formatMessage(data, msg) {
      return msg || `분류 모델 결과: ${data?.result}`;
    },
  },
  car: {
    id: 'car',
    label: '연비 효율 계산',
    type: 'regression',
    overlayId: 'overlay-car',
    formId: 'form-car',
    resultId: 'result-car',
    valueId: 'result-car-value',
    messageId: 'result-car-message',
    submitBtnId: 'btn-car-submit',
    api: '/api/ai/predict_car',
    fields: ['horsepower', 'weight', 'displacement', 'acceleration'],
    defaults: { horsepower: 100, weight: 3000, displacement: 200, acceleration: 15.0 },
    submitLabel: '연비 계산',
    loadingLabel: '계산 중…',
    formatResult(data) {
      const mpg = data?.mpg;
      return mpg != null ? `${mpg} MPG` : '—';
    },
    formatMessage(data, msg) {
      return msg || `회귀 모델 예측 연비: ${data?.mpg} MPG`;
    },
  },
};

let activeOverlay = null;

/* ── Overlay ── */
function openOverlay(overlayId) {
  closeAllOverlays();

  const overlay = document.getElementById(overlayId);
  if (!overlay) return;

  overlay.classList.add('is-open');
  overlay.setAttribute('aria-hidden', 'false');
  document.body.style.overflow = 'hidden';
  activeOverlay = overlay;

  const model = getModelByOverlay(overlayId);
  if (model) {
    const firstInput = document.querySelector(`#${model.formId} input`);
    if (firstInput) setTimeout(() => firstInput.focus(), 300);
  }
}

function closeOverlay(overlay) {
  if (!overlay) return;
  overlay.classList.remove('is-open');
  overlay.setAttribute('aria-hidden', 'true');
  if (activeOverlay === overlay) activeOverlay = null;
  if (!document.querySelector('.ai-overlay.is-open')) {
    document.body.style.overflow = '';
  }
}

function closeAllOverlays() {
  document.querySelectorAll('.ai-overlay.is-open').forEach(closeOverlay);
}

function getModelByOverlay(overlayId) {
  return Object.values(MODELS).find((m) => m.overlayId === overlayId);
}

function getModelByForm(form) {
  const modelId = form.dataset.model;
  return MODELS[modelId] || null;
}

/* ── Result UI ── */
function hideResult(model) {
  const box = document.getElementById(model.resultId);
  box.classList.remove('is-visible', 'is-loading', 'is-error');
}

function showLoading(model) {
  const box = document.getElementById(model.resultId);
  const valueEl = document.getElementById(model.valueId);
  const msgEl = document.getElementById(model.messageId);

  box.classList.add('is-visible', 'is-loading');
  box.classList.remove('is-error');
  valueEl.textContent = '';
  msgEl.textContent = `[${model.label}] ${model.loadingLabel}`;
}

function showSuccess(model, json) {
  const box = document.getElementById(model.resultId);
  const valueEl = document.getElementById(model.valueId);
  const msgEl = document.getElementById(model.messageId);

  box.classList.add('is-visible');
  box.classList.remove('is-loading', 'is-error');
  valueEl.textContent = model.formatResult(json.data);
  msgEl.textContent = model.formatMessage(json.data, json.message);
}

function showError(model, message) {
  const box = document.getElementById(model.resultId);
  const valueEl = document.getElementById(model.valueId);
  const msgEl = document.getElementById(model.messageId);

  box.classList.add('is-visible', 'is-error');
  box.classList.remove('is-loading');
  valueEl.textContent = '오류 발생';
  msgEl.textContent = `[${model.label}] ${message}`;
}

/* ── Form data ── */
function collectPayload(form, model) {
  const payload = {};

  for (const key of model.fields) {
    const input = form.elements[key];
    const raw = input?.value?.trim();

    if (raw === '' || raw == null) {
      payload[key] = model.defaults[key];
    } else {
      const num = parseFloat(raw);
      if (Number.isNaN(num)) {
        throw new Error(`${key} 값이 올바른 숫자가 아닙니다.`);
      }
      payload[key] = num;
    }
  }

  return payload;
}

/* ── API ── */
async function parseJsonResponse(response) {
  const text = await response.text();
  const contentType = response.headers.get('content-type') || '';

  if (!contentType.includes('application/json')) {
    throw new Error(
      `서버가 JSON 대신 HTML을 반환했습니다 (${response.status}). ` +
      `API 주소(${response.url})와 서버 실행 상태를 확인하세요.`
    );
  }

  try {
    return JSON.parse(text);
  } catch {
    throw new Error('서버 응답을 JSON으로 해석할 수 없습니다.');
  }
}

async function submitPrediction(model, form) {
  const submitBtn = document.getElementById(model.submitBtnId);
  const originalLabel = submitBtn.textContent;

  try {
    const payload = collectPayload(form, model);

    submitBtn.disabled = true;
    submitBtn.textContent = model.loadingLabel;
    showLoading(model);

    const response = await fetch(model.api, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-Model-Type': model.id,
      },
      body: JSON.stringify(payload),
    });

    const json = await parseJsonResponse(response);

    if (!response.ok || json.success === false) {
      throw new Error(json.message || `서버 오류 (${response.status})`);
    }

    showSuccess(model, json);
  } catch (err) {
    showError(model, err.message || '요청 처리 중 오류가 발생했습니다.');
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = originalLabel;
  }
}

/* ── Event bindings ── */
function init() {
  // 홈 카드 → 오버레이 열기
  document.querySelectorAll('[data-open]').forEach((btn) => {
    btn.addEventListener('click', () => {
      openOverlay(btn.dataset.open);
    });
  });

 

  // 폼 제출 — 모델별 분기
    Object.values(MODELS).forEach((model) => {
        const form = document.getElementById(model.formId);
        if (!form) return;

        form.addEventListener('submit', (e) => {
        e.preventDefault();
        submitPrediction(model, form);
        });

        form.addEventListener('reset', () => {
        hideResult(model);
        });

        const overlay = form.closest('.ai-overlay') || form.closest('.modal') || form.parentElement;

        if (overlay) {
            // 오버레이 영역 전체에서 data-close 속성을 가진 버튼을 모두 찾습니다.
            overlay.querySelectorAll('[data-close]').forEach((btn) => {
                btn.addEventListener('click', () => {
                    // 💡 1. 폼 강제 초기화 명령 (입력값 비우기 + hideResult 실행)
                    form.reset();
                    
                    // 💡 2. 오버레이 닫기 함수 호출
                    if (typeof closeOverlay === 'function') {
                        closeOverlay(overlay);
                    }
                });
            });
        }

        // ESC 닫기
     // ESC 키를 눌렀을 때도 팝업을 닫고 입력값을 초기화합니다.
        document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            // 1. 화면에 있는 모든 폼 요소를 찾습니다.
            const allForms = document.querySelectorAll('form');
            
            // 2. 모든 폼을 강제로 리셋시킵니다.
            // (이게 실행되면 우리가 등록해둔 'reset' 이벤트가 발동하여 hideResult도 자동으로 실행됩니다.)
            allForms.forEach((form) => {
                form.reset();
            });

            // 3. 마지막으로 기존에 쓰던 오버레이 닫기 기능을 실행합니다.
            if (typeof closeAllOverlays === 'function') {
                closeAllOverlays();
            }
        }
        });
    });
    }

document.addEventListener('DOMContentLoaded', init);
