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
    accuracyId: 'result-iris-accuracy', // 💡 추가: 정확도를 표시할 HTML 요소 ID
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
    accuracyId: 'result-car-accuracy', // 💡 추가: 정확도를 표시할 HTML 요소 ID
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
  const accuracyEl = document.getElementById(model.accuracyId); // 💡 추가
  const msgEl = document.getElementById(model.messageId);

  box.classList.add('is-visible', 'is-loading');
  box.classList.remove('is-error');
  valueEl.textContent = '';
  if (accuracyEl) accuracyEl.textContent = ''; // 💡 로딩 시 정확도 초기화
  msgEl.textContent = `[${model.label}] ${model.loadingLabel}`;
}

function showSuccess(model, json) {
  const box = document.getElementById(model.resultId);
  const valueEl = document.getElementById(model.valueId);
  const accuracyEl = document.getElementById(model.accuracyId); // 💡 추가
  const msgEl = document.getElementById(model.messageId);

  box.classList.add('is-visible');
  box.classList.remove('is-loading', 'is-error');
  
  // 결과 값 반영
  valueEl.textContent = model.formatResult(json.data);
  
  // 💡 추가: 정확도(accuracy) 데이터가 오면 화면에 퍼센트(%) 형태로 출력
  if (accuracyEl && json.data && json.data.accuracy != null) {
    const accuracyPercent = (json.data.accuracy * 100).toFixed(0);
    accuracyEl.textContent = `(모델 정확도: ${accuracyPercent}%)`;
  }
  
  msgEl.textContent = model.formatMessage(json.data, json.message);
}

function showError(model, message) {
  const box = document.getElementById(model.resultId);
  const valueEl = document.getElementById(model.valueId);
  const accuracyEl = document.getElementById(model.accuracyId); // 💡 추가
  const msgEl = document.getElementById(model.messageId);

  box.classList.add('is-visible', 'is-error');
  box.classList.remove('is-loading');
  valueEl.textContent = '오류 발생';
  if (accuracyEl) accuracyEl.textContent = ''; // 💡 에러 발생 시 정확도 초기화
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
      overlay.querySelectorAll('[data-close]').forEach((btn) => {
        btn.addEventListener('click', () => {
          form.reset();
          if (typeof closeOverlay === 'function') {
            closeOverlay(overlay);
          }
        });
      });
    }
  });

  // ESC 키 전역 바인딩 (루프 밖으로 한 번만 등록하도록 최적화)
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      document.querySelectorAll('form').forEach((form) => {
        form.reset();
      });
      if (typeof closeAllOverlays === 'function') {
        closeAllOverlays();
      }
    }
  });
}

document.addEventListener('DOMContentLoaded', init);