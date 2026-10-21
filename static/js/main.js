// Tailor Shop Client JavaScript
// Handles sidebar, modals, tab switching, RTL layout toggle, and dynamic measurement field filtering

document.addEventListener('DOMContentLoaded', () => {
    // 1. Mobile Sidebar Toggle
    const mobileToggleBtn = document.getElementById('mobileToggleBtn');
    const sidebar = document.getElementById('sidebar');

    if (mobileToggleBtn && sidebar) {
        mobileToggleBtn.addEventListener('click', () => {
            sidebar.classList.toggle('open');
        });

        document.addEventListener('click', (e) => {
            if (window.innerWidth <= 992) {
                if (!sidebar.contains(e.target) && !mobileToggleBtn.contains(e.target)) {
                    sidebar.classList.remove('open');
                }
            }
        });
    }

    // 2. Tab Navigation System
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const targetTab = button.getAttribute('data-tab');

            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));

            button.classList.add('active');
            const targetElement = document.getElementById(targetTab);
            if (targetElement) {
                targetElement.classList.add('active');
            }
        });
    });

    // 3. Modal Opening and Closing Helper Functions
    window.openModal = function(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.add('active');
        }
    };

    window.closeModal = function(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.remove('active');
        }
    };

    window.openEditCustomerModal = function(id, name, phone, address) {
        const form = document.getElementById('editCustomerForm');
        if (form) {
            form.action = `/customers/edit/${id}`;
            document.getElementById('edit_name').value = name || '';
            document.getElementById('edit_phone').value = phone || '';
            document.getElementById('edit_address').value = address || '';
        }
        openModal('editCustomerModal');
    };

    // 4. RTL / Urdu Layout Toggle Function
    window.toggleRtlLayout = function() {
        document.body.classList.toggle('rtl-mode');
        const langToggleText = document.getElementById('langToggleText');
        if (document.body.classList.contains('rtl-mode')) {
            if (langToggleText) langToggleText.textContent = 'English LTR';
        } else {
            if (langToggleText) langToggleText.textContent = 'Urdu RTL / اردو';
        }
    };

    // 5. Dynamic Garment Field Filter for Measurement Form
    const garmentSelect = document.getElementById('garment_type');
    if (garmentSelect) {
        const updateGarmentFields = () => {
            const selected = garmentSelect.value;
            const upperSection = document.getElementById('upper-body-section');
            const lowerSection = document.getElementById('lower-body-section');

            if (!upperSection || !lowerSection) return;

            if (selected === 'Shirt' || selected === 'Waistcoat') {
                upperSection.style.display = 'block';
                lowerSection.style.display = 'none';
            } else if (selected === 'Trouser') {
                upperSection.style.display = 'none';
                lowerSection.style.display = 'block';
            } else {
                // Kameez, Suit, Other -> Show both
                upperSection.style.display = 'block';
                lowerSection.style.display = 'block';
            }
        };

        garmentSelect.addEventListener('change', updateGarmentFields);
        // Initial run on load
        updateGarmentFields();
    }
});

// ==============================================================================
// Order Slip Functions (آرڈر پرچی)
// ==============================================================================

// 6. Calculate Balance = Total - Advance (live update)
function calculateBalance() {
    const priceInput = document.getElementById('price');
    const advanceInput = document.getElementById('advance');
    const balanceInput = document.getElementById('balance');

    // Skip if not on order slip page
    if (!priceInput || !advanceInput || !balanceInput) return;

    const total = parseFloat(priceInput.value) || 0;
    const advance = parseFloat(advanceInput.value) || 0;
    const balance = total - advance;

    // Show balance, minimum 0
    balanceInput.value = Math.max(0, balance);
}

// 7. Customer Dropdown Change: auto-fill phone + fetch latest measurements
function onCustomerChange(selectElement) {
    const selectedValue = selectElement.value;
    const phoneInput = document.getElementById('customer_phone');
    const newFields = document.getElementById('newCustomerFields');

    // If "Add New Customer" is selected
    if (selectedValue === '__new__') {
        if (newFields) newFields.classList.add('visible');
        if (phoneInput) {
            phoneInput.value = '';
            phoneInput.removeAttribute('readonly');
        }
        return;
    }

    // Hide new customer fields
    if (newFields) newFields.classList.remove('visible');

    // If empty selection, clear phone
    if (!selectedValue) {
        if (phoneInput) {
            phoneInput.value = '';
            phoneInput.setAttribute('readonly', true);
        }
        return;
    }

    // Auto-fill phone from dropdown data attribute
    const selectedOption = selectElement.options[selectElement.selectedIndex];
    if (phoneInput && selectedOption) {
        phoneInput.value = selectedOption.getAttribute('data-phone') || '';
        phoneInput.setAttribute('readonly', true);
    }

    // Fetch latest measurements from API and auto-fill fields
    fetch('/api/customer/' + selectedValue)
        .then(function(response) {
            return response.json();
        })
        .then(function(data) {
            if (data && data.phone && phoneInput) {
                phoneInput.value = data.phone;
                phoneInput.setAttribute('readonly', true);
            }
            // Auto-fill measurement fields if they exist on the page
            const fieldMap = {
                'neck': data.neck,
                'shoulder': data.shoulder,
                'chest': data.chest,
                'waist': data.waist,
                'sleeve': data.sleeve,
                'cuff': data.cuff,
                'shirt_length': data.shirt_length,
                'trouser_length': data.trouser_length,
                'trouser_waist': data.trouser_waist,
                'hip': data.hip,
                'thigh': data.thigh,
                'knee': data.knee,
                'bottom_paancha': data.bottom_paancha,
                'rise': data.rise,
            };
            for (const [fieldId, value] of Object.entries(fieldMap)) {
                const input = document.getElementById(fieldId);
                if (input && value !== undefined && value !== null) {
                    input.value = value;
                }
            }
        })
        .catch(function(err) {
            // Silently ignore API errors (measurements just won't auto-fill)
            console.log('Could not fetch customer measurements:', err);
        });
}

// ==============================================================================
// Single-Screen Urdu Desktop Order/Measurement Form JS Functions
// ==============================================================================

// 1. Search customer by Customer Number when Enter is pressed
function handleNumSearchEnter(event) {
    if (event.key === 'Enter') {
        event.preventDefault();
        searchByCustomerNumber();
    }
}

// 2. Fetch customer details by customer number and fill the form
function searchByCustomerNumber() {
    const input = document.getElementById('search_num_input');
    if (!input || !input.value.trim()) return;

    const num = input.value.trim();
    fetch('/api/customer/by-number/' + encodeURIComponent(num))
        .then(res => res.json())
        .then(data => {
            if (data.success && data.customer) {
                populateTailorForm(data.customer);
                showStatusToast('کسٹمر کا ریکارڈ لوڈ ہو گیا!', 'success');
            } else {
                showStatusToast('کسٹمر نمبر ' + num + ' نہیں ملا!', 'danger');
            }
        })
        .catch(err => {
            console.error(err);
            showStatusToast('نیٹ ورک کی غلطی۔ دوبارہ کوشش کریں۔', 'danger');
        });
}

// 3. Live Search by Name or Phone with suggestion list
function handleLiveSearch(query) {
    const listContainer = document.getElementById('liveSearchDropdown');
    if (!listContainer) return;

    if (!query || query.trim().length === 0) {
        listContainer.style.display = 'none';
        return;
    }

    fetch('/api/customers/live-search?q=' + encodeURIComponent(query.trim()))
        .then(res => res.json())
        .then(data => {
            if (!data || data.length === 0) {
                listContainer.innerHTML = '<div class="live-search-item">کوئی کسٹمر نہیں ملا</div>';
                listContainer.style.display = 'block';
                return;
            }

            let html = '';
            data.forEach(cust => {
                html += `<div class="live-search-item" onclick="selectLiveCustomer('${cust.customer_number}')">
                    <span><b>${cust.name}</b> (${cust.phone || 'کوئی فون نہیں'})</span>
                    <span class="green-number-box" style="font-size: 0.8rem; padding: 1px 6px;">${cust.customer_number}</span>
                </div>`;
            });
            listContainer.innerHTML = html;
            listContainer.style.display = 'block';
        })
        .catch(err => console.error(err));
}

// Helper when a customer is clicked from the live search dropdown
function selectLiveCustomer(custNumber) {
    const listContainer = document.getElementById('liveSearchDropdown');
    if (listContainer) listContainer.style.display = 'none';
    const numInput = document.getElementById('search_num_input');
    if (numInput) numInput.value = custNumber;
    searchByCustomerNumber();
}

// 4. Fill form inputs from customer object
function populateTailorForm(cust) {
    document.getElementById('name').value = cust.name || '';
    document.getElementById('phone').value = cust.phone || '';
    document.getElementById('address').value = cust.address || '';
    document.getElementById('customer_number').value = cust.customer_number || '';
    document.getElementById('badge_customer_number').textContent = cust.customer_number || '';

    // Show customer number badge wrap when customer is loaded via search
    const badgeWrap = document.getElementById('cust_badge_wrap');
    if (badgeWrap) badgeWrap.style.display = 'flex';

    const m = cust.measurements || {};
    
    // Shirts
    const shirtFields = ['shirt_length', 'sleeve', 'shoulder', 'collar_size', 'chest', 'armpit', 'daaman'];
    shirtFields.forEach(f => {
        const input = document.getElementById(f);
        if (input) input.value = m[f] || '';
    });

    // Daaman radio
    const daamanType = m['daaman_type'] || 'دامن گول';
    const radios = document.getElementsByName('daaman_type');
    for (let r of radios) {
        r.checked = (r.value === daamanType);
    }

    // Shalwar
    const shalwarFields = ['shalwar_length', 'paancha', 'asan', 'shalwar_gheer', 'chaak'];
    shalwarFields.forEach(f => {
        const input = document.getElementById(f);
        if (input) input.value = m[f] || '';
    });

    // Dropdowns
    const dropdownFields = ['patti', 'patti_size', 'patti_length', 'paancha_patti', 'stitching', 'extra_1', 'extra_2', 'cuff_type', 'cuff_size', 'collar_nok', 'moora'];
    dropdownFields.forEach(f => {
        const input = document.getElementById(f);
        if (input) input.value = m[f] || '';
    });

    // Checkboxes
    const checkFields = [
        'baghair_plate', 'baghair_label', 'chaak_patti_button', 'chamak_taar', 'steel_button',
        'front_pocket', 'side_pocket_1', 'side_pocket_2', 'shalwar_pocket',
        'front_pocket_kaaj', 'cuff_1_kaaj', 'cuff_2_kaaj', 'stud_kaaj'
    ];
    checkFields.forEach(f => {
        const chk = document.querySelector(`input[name="${f}"]`);
        if (chk) chk.checked = !!m[f];
    });
}

// 5. Refresh form for a new customer
function refreshFormForNewCustomer() {
    document.getElementById('tailorForm').reset();
    document.getElementById('customer_number').value = '';
    document.getElementById('badge_customer_number').textContent = '';
    const badgeWrap = document.getElementById('cust_badge_wrap');
    if (badgeWrap) badgeWrap.style.display = 'none';
    // Reset dirty flag so no warning shows after reset
    formIsDirty = false;
    showStatusToast('نیا فارم تیار ہے۔', 'success');
}

// 6. Print Slip Modal Handler
function openUrduPrintSlipModal() {
    const custNum = document.getElementById('customer_number').value || '--';
    const name = document.getElementById('name').value || '--';
    const phone = document.getElementById('phone').value || '--';
    const address = document.getElementById('address').value || '--';

    document.getElementById('slip_c_num').textContent = custNum;
    document.getElementById('slip_date').textContent = new Date().toLocaleDateString('ur-PK');
    document.getElementById('slip_name').textContent = name;
    document.getElementById('slip_phone').textContent = phone;
    document.getElementById('slip_address').textContent = address;

    // Fill measurements table
    document.getElementById('slip_shirt_length').textContent = document.getElementById('shirt_length').value || '-';
    document.getElementById('slip_sleeve').textContent = document.getElementById('sleeve').value || '-';
    document.getElementById('slip_shoulder').textContent = document.getElementById('shoulder').value || '-';
    document.getElementById('slip_collar_size').textContent = document.getElementById('collar_size').value || '-';
    document.getElementById('slip_chest').textContent = document.getElementById('chest').value || '-';
    document.getElementById('slip_armpit').textContent = document.getElementById('armpit').value || '-';
    document.getElementById('slip_daaman').textContent = document.getElementById('daaman').value || '-';

    const daamanRadio = document.querySelector('input[name="daaman_type"]:checked');
    document.getElementById('slip_daaman_type').textContent = daamanRadio ? daamanRadio.value : '-';

    document.getElementById('slip_shalwar_length').textContent = document.getElementById('shalwar_length').value || '-';
    document.getElementById('slip_paancha').textContent = document.getElementById('paancha').value || '-';
    document.getElementById('slip_asan').textContent = document.getElementById('asan').value || '-';
    document.getElementById('slip_shalwar_gheer').textContent = document.getElementById('shalwar_gheer').value || '-';
    document.getElementById('slip_chaak').textContent = document.getElementById('chaak').value || '-';

    // Tags
    let tagsHtml = '';
    const dropdowns = ['patti', 'stitching', 'cuff_type', 'collar_nok', 'extra_1', 'extra_2'];
    dropdowns.forEach(f => {
        const val = document.getElementById(f)?.value;
        if (val) tagsHtml += `<span class="tag-badge">${val}</span>`;
    });

    const checkLabels = {
        'baghair_plate': 'بغیر پلیٹ', 'baghair_label': 'بغیر لیبل', 'chaak_patti_button': 'چاک پٹی بٹن',
        'chamak_taar': 'چمک تار', 'steel_button': 'سٹیل بٹن', 'front_pocket': 'سامنے پاکٹ',
        'side_pocket_1': 'سائیڈ پاکٹ 1', 'side_pocket_2': 'سائیڈ پاکٹ 2', 'shalwar_pocket': 'شلوار پاکٹ',
        'front_pocket_kaaj': 'سامنے پاکٹ کاج', 'cuff_1_kaaj': 'کف ایک کاج', 'cuff_2_kaaj': 'کف دو کاج', 'stud_kaaj': 'سٹڈ کاج'
    };
    Object.keys(checkLabels).forEach(key => {
        const chk = document.querySelector(`input[name="${key}"]`);
        if (chk && chk.checked) {
            tagsHtml += `<span class="tag-badge">${checkLabels[key]}</span>`;
        }
    });

    document.getElementById('slip_design_tags').innerHTML = tagsHtml || '<span>عام انداز</span>';
    document.getElementById('printSlipModal').style.display = 'flex';
}

function closeUrduPrintSlipModal() {
    document.getElementById('printSlipModal').style.display = 'none';
}

// Validation before form submit
function validateTailorForm() {
    const name = document.getElementById('name').value.trim();
    const phone = document.getElementById('phone').value.trim();
    if (!name || !phone) {
        showStatusToast('نام اور فون نمبر درج کرنا لازمی ہیں!', 'danger');
        if (!name) document.getElementById('name').focus();
        else document.getElementById('phone').focus();
        return false;
    }
    // Mark as clean — user clicked Save, so no warning needed on redirect
    formIsDirty = false;
    return true;
}

// Toast Status Message helper
function showStatusToast(msg, type = 'success') {
    const alertBox = document.getElementById('statusAlert');
    if (!alertBox) return;
    alertBox.className = 'desktop-alert alert-' + type;
    alertBox.textContent = msg;
    alertBox.style.display = 'block';
    setTimeout(() => {
        alertBox.style.display = 'none';
    }, 4000);
}

// ==============================================================================
// UNSAVED-CHANGES GUARD
// Tracks whether the admin has typed anything in the form.
// Shows an Urdu confirm dialog if they try to leave without saving.
// ==============================================================================

// Flag: true = form has unsaved data
let formIsDirty = false;

// Mark dirty as soon as any input/checkbox/select changes
document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('tailorForm');
    if (!form) return;

    // Listen for any change inside the form
    form.addEventListener('input', function () { formIsDirty = true; });
    form.addEventListener('change', function () { formIsDirty = true; });

    // Browser back / close / refresh — show native dialog
    window.addEventListener('beforeunload', function (e) {
        if (formIsDirty) {
            // Modern browsers show their own text; we set ours as fallback
            e.preventDefault();
            e.returnValue = 'کیا آپ محفوظ کیے بغیر جانا چاہتے ہیں؟';
            return e.returnValue;
        }
    });

    // In-app navigation links (واپس, لسٹ, ختم کریں)
    // Intercept clicks on <a> tags inside the page
    document.addEventListener('click', function (e) {
        const link = e.target.closest('a[href]');
        if (!link) return;                        // not a link
        if (!formIsDirty) return;                 // nothing typed yet
        if (link.target === '_blank') return;     // new tab, ignore

        // Don't intercept the form's own submit
        const href = link.getAttribute('href');
        if (!href || href === '#') return;

        // Ask the user in Urdu
        const ok = window.confirm('کیا آپ محفوظ کیے بغیر جانا چاہتے ہیں؟\nآپ کا ڈیٹا محفوظ نہیں ہوگا۔');
        if (!ok) {
            e.preventDefault(); // stay on the page
        }
        // If ok = true, let the navigation happen normally
    });
});
