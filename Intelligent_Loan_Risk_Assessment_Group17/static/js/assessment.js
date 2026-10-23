// Progressive enhancement: without JavaScript the complete form remains usable.
const wizard = document.querySelector('#assessment-form');
if (wizard) {
    let step = 0;
    const panels = [...wizard.querySelectorAll('[data-step]')];
    const purpose = wizard.elements.loan_intent;
    const next = document.querySelector('#next-step');
    const previous = document.querySelector('#previous-step');
    const submit = document.querySelector('#submit-assessment');
    const money = new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 });
    const labelFor = field => field.closest('label').childNodes[0].textContent.trim();
    const visibleFields = () => [...wizard.querySelectorAll('input, select')].filter(field => !field.disabled && !field.closest('[hidden]'));
    const valueFor = field => {
        if (!field.value) return 'Not entered';
        if (field.tagName === 'SELECT') return field.selectedOptions[0].textContent;
        if (/income|debt|amnt/.test(field.name)) return money.format(Number(field.value));
        return field.value;
    };
    const addPair = (list, label, value) => {
        const dt = document.createElement('dt'); dt.textContent = label;
        const dd = document.createElement('dd'); dd.textContent = value;
        list.append(dt, dd);
    };
    const summary = () => {
        const list = document.querySelector('#live-summary'); list.replaceChildren();
        ['loan_intent', 'loan_amnt', 'person_income'].forEach(name => {
            const field = wizard.elements[name]; addPair(list, labelFor(field), valueFor(field));
        });
        if (Number(wizard.elements.person_income.value) > 0 && Number(wizard.elements.loan_amnt.value) > 0) {
            addPair(list, 'Loan / annual income', `${(100 * Number(wizard.elements.loan_amnt.value) / Number(wizard.elements.person_income.value)).toFixed(1)}%`);
        }
    };
    const review = () => {
        const container = document.querySelector('#review-summary'); container.replaceChildren();
        panels.filter(panel => panel.dataset.step !== '2').forEach(panel => {
            if (panel.id === 'secondary-applicant' && purpose.value !== 'EDUCATION') return;
            if (panel.id === 'other-loan-details' && purpose.value !== 'OTHER') return;
            const heading = document.createElement('h4'); heading.textContent = panel.querySelector('h3').childNodes[0].textContent;
            const list = document.createElement('dl'); list.className = 'review-list';
            panel.querySelectorAll('input, select').forEach(field => {
                if (!field.closest('label').hidden) addPair(list, labelFor(field), valueFor(field));
            });
            container.append(heading, list);
        });
    };
    const show = (focus = true) => {
        panels.forEach(panel => {
            panel.hidden = Number(panel.dataset.step) !== step ||
                (panel.id === 'secondary-applicant' && purpose.value !== 'EDUCATION') ||
                (panel.id === 'other-loan-details' && purpose.value !== 'OTHER');
        });
        wizard.querySelectorAll('[data-step-label]').forEach((item, index) => {
            if (index === step) item.setAttribute('aria-current', 'step'); else item.removeAttribute('aria-current');
            item.classList.toggle('complete', index < step);
        });
        previous.hidden = step === 0; next.hidden = step === 2; submit.hidden = step !== 2;
        next.textContent = step === 1 ? 'Review assessment →' : 'Continue to applicant →';
        if (step === 2) review();
        summary();
        if (focus) panels.find(panel => !panel.hidden)?.querySelector('h3').focus();
    };
    const check = fields => {
        let first;
        fields.forEach(field => {
            const error = document.getElementById(`${field.id}-error`);
            const valid = field.checkValidity();
            field.setAttribute('aria-invalid', String(!valid));
            error.textContent = valid ? '' : field.validationMessage;
            if (!valid && !first) first = field;
        });
        if (first) { first.focus(); document.querySelector('#form-status').textContent = 'Check the highlighted fields before continuing.'; }
        else document.querySelector('#form-status').textContent = '';
        return !first;
    };
    wizard.querySelectorAll('input, select').forEach(field => {
        field.id ||= `field-${field.name}`;
        const error = document.createElement('span'); error.id = `${field.id}-error`; error.className = 'field-error';
        field.closest('label').append(error);
        const hint = field.closest('label').querySelector('.field-hint');
        if (hint) hint.id = `${field.id}-hint`;
        field.setAttribute('aria-describedby', [hint?.id, error.id].filter(Boolean).join(' '));
        field.addEventListener('input', () => { if (field.getAttribute('aria-invalid') === 'true') check([field]); });
    });
    wizard.noValidate = true;
    wizard.querySelector('.form-progress').hidden = false;
    document.querySelector('#load-demo').hidden = false;
    next.addEventListener('click', () => { if (check(visibleFields())) { step++; show(); } });
    previous.addEventListener('click', () => { step--; show(); });
    document.querySelector('#edit-review').addEventListener('click', () => { step = 1; show(); });
    purpose.addEventListener('change', () => show(false));
    wizard.addEventListener('input', summary);
    wizard.addEventListener('reset', () => setTimeout(() => {
        wizard.querySelectorAll('input, select').forEach(field => { field.value = ''; field.removeAttribute('aria-invalid'); });
        wizard.querySelectorAll('.field-error').forEach(error => { error.textContent = ''; });
        document.querySelector('#form-status').textContent = '';
        purpose.dispatchEvent(new Event('change')); step = 0; show();
    }, 0));
    document.querySelector('#load-demo').addEventListener('click', () => {
        const sample = JSON.parse(document.querySelector('#demo-sample').textContent);
        Object.entries(sample).forEach(([name, value]) => { if (wizard.elements[name]) wizard.elements[name].value = value; });
        wizard.querySelectorAll('.field-error').forEach(error => { error.textContent = ''; });
        wizard.querySelectorAll('[aria-invalid]').forEach(field => field.removeAttribute('aria-invalid'));
        purpose.dispatchEvent(new Event('change')); step = 0; show(false);
        document.querySelector('#form-status').textContent = 'Demo example loaded. These are fictional applicant details.';
    });
    wizard.addEventListener('submit', event => {
        if (step !== 2) { event.preventDefault(); next.click(); return; }
        // Recheck every active step, including after editing inputs.
        for (let index = 0; index < 2; index++) {
            step = index; show(false);
            if (!check(visibleFields())) { event.preventDefault(); return; }
        }
        step = 2; show(false);
        submit.disabled = true; submit.textContent = 'Preparing your result…';
        wizard.setAttribute('aria-busy', 'true');
    });
    window.addEventListener('pageshow', () => { submit.disabled = false; wizard.removeAttribute('aria-busy'); submit.textContent = purpose.value === 'OTHER' ? 'Preview Loan Details' : 'Assess Loan Risk'; });
    show(false);
}
document.querySelector('#print-result')?.addEventListener('click', () => window.print());
