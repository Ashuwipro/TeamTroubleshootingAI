// Generate File Module - Handles all payment file generation functionality

const GenerateFileModule = {
    generateModal: null,

    init() {
        this.generateModal = document.getElementById('generateModal');
        this.setupEventListeners();
    },

    setupEventListeners() {
        // Mix File checkbox event listener
        const checkbox = document.getElementById('mixFileCheckbox');
        if (checkbox) {
            checkbox.addEventListener('change', this.handleMixFileCheckbox.bind(this));
        }
    },

    handleMixFileCheckbox(e) {
        const mixFileDropdowns = document.getElementById('mixFileDropdowns');
        const mixFile3Container = document.getElementById('mixFile3Container');
        const addBtn = document.getElementById('mixFileAddBtn');

        if (e.target.checked) {
            mixFileDropdowns.style.display = 'flex';
            mixFile3Container.style.display = 'none';
            addBtn.style.display = 'inline-block';
            addBtn.textContent = 'Add';
        } else {
            mixFileDropdowns.style.display = 'none';
            mixFile3Container.style.display = 'none';
            addBtn.style.display = 'inline-block';
            addBtn.textContent = 'Add';
        }
    },

    openModal() {
        this.generateModal.classList.add('show');
        this.loadFormFields();
        document.getElementById('fileTypeSelect').addEventListener('change', this.loadFormFields.bind(this));
    },

    closeModal() {
        this.generateModal.classList.remove('show');
        document.getElementById('mixFileCheckbox').checked = false;
        document.getElementById('mixFileDropdowns').style.display = 'none';
        document.getElementById('mixFile3Container').style.display = 'none';
        document.getElementById('mixFileAddBtn').textContent = 'Add';
    },

    loadFormFields() {
        const modalBody = document.getElementById('modalBody');
        modalBody.innerHTML = '';
        const fileType = document.getElementById('fileTypeSelect').value;
        let fields = [];
        let isCheckForm = false;

        if (fileType === 'ACH NACHA XML') {
            fields = [
                { label: 'Batches Quantity', name: 'batchesQuantity', type: 'number' },
                { label: 'Transactions Count', name: 'transactionsCount', type: 'number' },
                { label: 'ACH Comp IDs', name: 'achCompIds', type: 'text' },
                { label: 'ACH Comp Names', name: 'achCompNames', type: 'text' },
                { label: 'ABAs', name: 'abas', type: 'text' }
            ];
        } else if (fileType === 'CHECKS XML') {
            isCheckForm = true;
            fields = [
                { label: 'Batches Quantity', name: 'batchesQuantity', type: 'number' },
                { label: 'Transactions Count', name: 'transactionsCount', type: 'number' }
            ];
        } else {
            modalBody.innerHTML = '<p style="text-align: center; color: #ffffff; font-size: 16px;">Coming soon...</p>';
            return;
        }

        const leftColumn = document.createElement('div');
        leftColumn.className = 'formColumn';
        leftColumn.style.borderRight = '1px solid #555';
        leftColumn.style.paddingRight = '15px';

        const middleColumn = document.createElement('div');
        middleColumn.className = 'formColumn';
        middleColumn.style.borderRight = '1px solid #555';
        middleColumn.style.paddingRight = '15px';

        const babMessage = document.createElement('div');
        babMessage.style.cssText = 'color: #ffffff; font-size: 14px; margin-bottom: 15px; font-style: italic;';
        babMessage.textContent = 'Only applicable with BAB (optional).';
        middleColumn.appendChild(babMessage);

        const payeeIdsGroup = document.createElement('div');
        payeeIdsGroup.className = 'formGroup';
        const payeeIdsLabel = document.createElement('label');
        payeeIdsLabel.className = 'formLabel';
        payeeIdsLabel.textContent = 'Payee IDs:';
        const payeeIdsTagInput = this.createTagInput('payeeIds', 'Enter Payee IDs...', false);
        payeeIdsTagInput.style.flex = '1';
        payeeIdsGroup.appendChild(payeeIdsLabel);
        payeeIdsGroup.appendChild(payeeIdsTagInput);
        middleColumn.appendChild(payeeIdsGroup);

        const lookupTypeGroup = document.createElement('div');
        lookupTypeGroup.className = 'formGroup';
        lookupTypeGroup.innerHTML = `
            <label class="formLabel">Payee Lookup Type:</label>
            <select class="formInput" name="payeeLookupType">
                <option value="No Flag">No Flag</option>
                <option value="DB">DB</option>
                <option value="FILE">FILE</option>
                <option value="NONE">NONE</option>
            </select>
        `;
        middleColumn.appendChild(lookupTypeGroup);

        const lookupElementsGroup = document.createElement('div');
        lookupElementsGroup.className = 'formGroup';
        lookupElementsGroup.innerHTML = `
            <label class="formLabel">Payee Lookup Elements:</label>
            <div class="customSelect">
                <div class="selectTrigger" id="payeeLookupTrigger">Select Payee Lookups</div>
                <div class="selectOptions" id="payeeLookupOptions" style="display: none;">
                    <label><input type="checkbox" value="PayeeID" onchange="updateSelection()"> PayeeID</label>
                    <label><input type="checkbox" value="PayeeName1" onchange="updateSelection()"> PayeeName1</label>
                    <label><input type="checkbox" value="PayeeAddress1" onchange="updateSelection()"> PayeeAddress1</label>
                    <label><input type="checkbox" value="AccountNumber" onchange="updateSelection()"> AccountNumber</label>
                    <label><input type="checkbox" value="ABA" onchange="updateSelection()"> ABA</label>
                    <label><input type="checkbox" value="NachaTranType" onchange="updateSelection()"> NachaTranType</label>
                    <label><input type="checkbox" value="PayeeEmail" onchange="updateSelection()"> PayeeEmail</label>
                </div>
            </div>
            <input type="hidden" name="payeeLookupElements" id="payeeLookupElementsHidden">
        `;
        middleColumn.appendChild(lookupElementsGroup);

        const rightColumn = document.createElement('div');
        rightColumn.className = 'formColumn';

        const valueMessage = document.createElement('div');
        valueMessage.style.cssText = 'color: #ffffff; font-size: 14px; margin-bottom: 15px; font-style: italic;';
        valueMessage.textContent = 'Only one value is allowed';
        rightColumn.appendChild(valueMessage);

        const clientCompanyGroup = document.createElement('div');
        clientCompanyGroup.className = 'formGroup';
        clientCompanyGroup.innerHTML = `
            <label class="formLabel">Client Company:</label>
            <input type="text" class="formInput" name="clientCompany" placeholder="Enter Client Company">
        `;
        rightColumn.appendChild(clientCompanyGroup);

        const bankNameGroup = document.createElement('div');
        bankNameGroup.className = 'formGroup';
        bankNameGroup.innerHTML = `
            <label class="formLabel">Bank Name:</label>
            <input type="text" class="formInput" name="bankName" placeholder="Enter Bank Name">
        `;
        rightColumn.appendChild(bankNameGroup);

        const typeGroup = document.createElement('div');
        typeGroup.className = 'formGroup';
        typeGroup.innerHTML = `
            <label class="formLabel">Type:</label>
            <select class="formInput" name="type">
                <option value="CCD">CCD</option>
                <option value="CTX">CTX</option>
                <option value="PPD">PPD</option>
                <option value="IAT">IAT</option>
            </select>
        `;
        rightColumn.appendChild(typeGroup);

        const optionsGroup = document.createElement('div');
        optionsGroup.className = 'formGroup';
        optionsGroup.innerHTML = `
            <label class="formLabel">Options:</label>
            <select class="formInput" name="options" id="optionsSelect">
                <option value="ACH">ACH</option>
                <option value="ACH & ESend">ACH & ESend</option>
                <option value="ESend_Only">ESend_Only</option>
            </select>
        `;
        rightColumn.appendChild(optionsGroup);

        const esendDetails = document.createElement('div');
        esendDetails.id = 'esendDetails';
        esendDetails.style.display = 'none';
        esendDetails.style.marginTop = '20px';

        const esendMessage = document.createElement('div');
        esendMessage.style.cssText = 'color: #ffffff; font-size: 14px; margin-bottom: 15px; font-style: italic;';
        esendMessage.textContent = 'ESend Details';
        esendDetails.appendChild(esendMessage);

        const esendAppGroup = document.createElement('div');
        esendAppGroup.className = 'formGroup';
        esendAppGroup.style.marginBottom = '10px';
        esendAppGroup.innerHTML = `
            <label class="formLabel">ESend App:</label>
            <div style="display: flex; gap: 10px; flex: 1;">
                <select class="formInput" name="esendAppType" style="flex: 0 0 100px;">
                    <option value="Name">Name</option>
                    <option value="ID">ID</option>
                </select>
                <input type="text" class="formInput" name="esendAppValue" placeholder="Enter ESend App" style="flex: 1;">
            </div>
        `;
        esendDetails.appendChild(esendAppGroup);

        const esendProfileKeysGroup = document.createElement('div');
        esendProfileKeysGroup.className = 'formGroup';
        esendProfileKeysGroup.style.marginBottom = '10px';
        esendProfileKeysGroup.innerHTML = `
            <label class="formLabel">ESend Profile Keys:</label>
            <input type="text" class="formInput" name="esendProfileKeys" placeholder="Enter ESend Profile Keys">
        `;
        esendDetails.appendChild(esendProfileKeysGroup);

        const payeeEmailsGroup = document.createElement('div');
        payeeEmailsGroup.className = 'formGroup';
        payeeEmailsGroup.innerHTML = `
            <label class="formLabel">Payee Emails:</label>
            <input type="text" class="formInput" name="payeeEmails" placeholder="Enter Payee Emails">
        `;
        esendDetails.appendChild(payeeEmailsGroup);

        rightColumn.appendChild(esendDetails);

        fields.forEach((field, index) => {
            const formGroup = document.createElement('div');
            formGroup.className = 'formGroup';

            if (['achCompIds', 'achCompNames', 'abas'].includes(field.name)) {
                const label = document.createElement('label');
                label.className = 'formLabel';
                label.textContent = field.label + ':';

                const tagInput = this.createTagInput(field.name, `Enter ${field.label}...`, true);
                tagInput.style.flex = '1';

                formGroup.appendChild(label);
                formGroup.appendChild(tagInput);
            } else {
                formGroup.innerHTML = `
                    <label class="formLabel">${field.label}:</label>
                    <input type="${field.type}" class="formInput" name="${field.name}" placeholder="Enter ${field.label}">
                `;
            }

            leftColumn.appendChild(formGroup);

            if (index === 0) {
                const messageDiv = document.createElement('div');
                messageDiv.style.cssText = 'color: #ffffff; font-size: 12px; margin: 5px 0; padding-left: 165px;';
                messageDiv.textContent = 'You can provide either one or more values separated by commas';
                leftColumn.appendChild(messageDiv);
            }
        });

        // Add Check form specific fields
        if (isCheckForm) {
            const checkOrderGroup = document.createElement('div');
            checkOrderGroup.className = 'formGroup';
            checkOrderGroup.innerHTML = `
                <label class="formLabel">Check Order:</label>
                <select class="formInput" name="checkOrder">
                    <option value="None - start from 1000">None - start from 1000</option>
                    <option value="Ascending">Ascending</option>
                    <option value="Descending">Descending</option>
                    <option value="Random">Random</option>
                </select>
            `;
            leftColumn.appendChild(checkOrderGroup);

            const checkAppGroup = document.createElement('div');
            checkAppGroup.className = 'formGroup';
            checkAppGroup.innerHTML = `
                <label class="formLabel">Check App:</label>
                <div style="display: flex; gap: 10px; flex: 1;">
                    <select class="formInput" name="checkAppType" style="flex: 0 0 100px;">
                        <option value="Name">Name</option>
                        <option value="ID">ID</option>
                    </select>
                    <input type="text" class="formInput" name="checkAppValue" placeholder="Enter Check App" style="flex: 1;">
                </div>
            `;
            leftColumn.appendChild(checkAppGroup);

            const checkProfilesGroup = document.createElement('div');
            checkProfilesGroup.className = 'formGroup';
            checkProfilesGroup.innerHTML = `
                <label class="formLabel">Check Profiles:</label>
                <input type="text" class="formInput" name="checkProfiles" placeholder="Enter Check Profiles (comma separated)">
            `;
            leftColumn.appendChild(checkProfilesGroup);
        }

        modalBody.appendChild(leftColumn);

        // Only add middle and right columns for ACH NACHA form
        if (!isCheckForm) {
            modalBody.appendChild(middleColumn);
            modalBody.appendChild(rightColumn);
        }

        const trigger = document.getElementById('payeeLookupTrigger');
        const options = document.getElementById('payeeLookupOptions');

        if (trigger && options && !isCheckForm) {
            trigger.addEventListener('click', function() {
                options.style.display = options.style.display === 'none' || options.style.display === '' ? 'block' : 'none';
            });

            document.addEventListener('click', function(event) {
                if (!trigger.contains(event.target) && !options.contains(event.target)) {
                    options.style.display = 'none';
                }
            });
        }

        const optionsSelect = document.getElementById('optionsSelect');
        if (optionsSelect && !isCheckForm) {
            optionsSelect.addEventListener('change', function() {
                const esendDetails = document.getElementById('esendDetails');
                if (this.value === 'ESend_Only' || this.value === 'ACH & ESend') {
                    esendDetails.style.display = 'block';
                } else {
                    esendDetails.style.display = 'none';
                }
            });
        }
    },

    createTagInput(fieldName, placeholder = 'Enter values separated by commas', allowDuplicates = false) {
        const container = document.createElement('div');
        container.className = 'tagInputContainer';
        container.dataset.fieldName = fieldName;
        container.style.cursor = 'text';

        const input = document.createElement('input');
        input.type = 'text';
        input.className = 'tagInputField';
        input.placeholder = placeholder;
        input.dataset.fieldName = fieldName;

        let tags = [];

        input.addEventListener('keydown', function(e) {
            if (e.key === ',' || e.key === 'Enter') {
                e.preventDefault();
                const value = this.value.trim().replace(/,+$/, '').trim();
                if (value) {
                    addTag(value);
                    this.value = '';
                }
            }
        });

        input.addEventListener('paste', function(e) {
            setTimeout(() => {
                let value = this.value.trim();
                const values = value.split(',').map(v => v.trim()).filter(v => v);
                if (values.length > 1) {
                    this.value = values[values.length - 1];
                    values.slice(0, -1).forEach(v => addTag(v));
                }
            }, 10);
        });

        const addTag = (text) => {
            if (!text) return;
            if (!allowDuplicates && tags.includes(text)) return;

            tags.push(text);

            const tag = document.createElement('span');
            tag.className = 'tag';

            const tagText = document.createElement('span');
            tagText.textContent = text;

            const removeBtn = document.createElement('span');
            removeBtn.className = 'tagRemoveBtn';
            removeBtn.textContent = '×';
            removeBtn.style.cursor = 'pointer';

            removeBtn.addEventListener('click', function() {
                const index = tags.indexOf(text);
                if (index > -1) {
                    tags.splice(index, 1);
                }
                tag.remove();
                input.focus();
                updateHiddenInput();
            });

            tag.appendChild(tagText);
            tag.appendChild(removeBtn);
            container.insertBefore(tag, input);

            updateHiddenInput();
        };

        const updateHiddenInput = () => {
            container.dataset.tags = JSON.stringify(tags);
        };

        container.addEventListener('click', function() {
            input.focus();
        });

        container.appendChild(input);
        return container;
    }
};

// Global functions for backwards compatibility
function openGenerateModal() {
    GenerateFileModule.openModal();
}

function closeGenerateModal() {
    GenerateFileModule.closeModal();
}

function addMixFileDropdown() {
    const mixFile3Container = document.getElementById('mixFile3Container');
    const addBtn = document.getElementById('mixFileAddBtn');

    if (mixFile3Container.style.display === 'none') {
        mixFile3Container.style.display = 'flex';
        addBtn.style.display = 'none';
    }
}

function removeMixFileDropdown() {
    const mixFile3Container = document.getElementById('mixFile3Container');
    const addBtn = document.getElementById('mixFileAddBtn');

    mixFile3Container.style.display = 'none';
    addBtn.style.display = 'inline-block';
}

async function generateFile() {
    const inputs = document.querySelectorAll('#modalBody .formInput, #modalBody input[type="hidden"]');
    const tagContainers = document.querySelectorAll('#modalBody .tagInputContainer');
    const fileType = document.getElementById('fileTypeSelect').value;
    const data = { fileType: fileType };

    inputs.forEach(input => {
        if (input.name) {
            data[input.name] = input.value;
        }
    });

    tagContainers.forEach(container => {
        const fieldName = container.dataset.fieldName;
        const tags = JSON.parse(container.dataset.tags || '[]');
        data[fieldName] = tags.join(',');
    });

    try {
        const response = await fetch('/generate-xml', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;

            const userGroup = data.clientCompany || 'UNKNOWN';
            const bankName = data.bankName || 'UNKNOWN';
            const now = new Date();
            const date = now.toISOString().split('T')[0].replace(/-/g, '');
            const time = now.toTimeString().split(' ')[0].replace(/:/g, '');
            const filename = `${userGroup}_${bankName}_ACHXML_${date}_${time}.xml`;

            a.download = filename;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);

            showSuccessPopup(filename);
            GenerateFileModule.closeModal();
        } else {
            const errorData = await response.json();
            addMessage(`Error: ${errorData.error || 'Unable to generate file'}`, false);
        }
    } catch (error) {
        addMessage(`Error: ${error.message}`, false);
    }
}

function showSuccessPopup(filename) {
    const successModal = document.createElement('div');
    successModal.className = 'modal show';
    successModal.id = 'successModal';
    successModal.style.zIndex = '3000';
    successModal.onclick = function(event) {
        if (event.target === successModal) {
            successModal.remove();
            addMessage('File generated successfully!', false);
        }
    };

    const successContent = document.createElement('div');
    successContent.className = 'modalContent';
    successContent.style.maxWidth = '500px';
    successContent.style.textAlign = 'center';

    const successHeader = document.createElement('div');
    successHeader.style.cssText = 'padding: 20px; border-bottom: 1px solid #444;';
    successHeader.innerHTML = `<h2 style="margin: 0; color: #4CAF50; font-size: 24px;">✓ File Generated Successfully</h2>`;

    const successBody = document.createElement('div');
    successBody.style.cssText = 'padding: 30px 20px; display: flex; flex-direction: column; gap: 20px;';

    const filenameDiv = document.createElement('div');
    filenameDiv.style.cssText = 'background-color: #1e1e1e; padding: 15px; border-radius: 5px; border: 1px solid #555;';
    filenameDiv.innerHTML = `
        <div style="color: #888; font-size: 12px; margin-bottom: 5px;">Filename:</div>
        <div style="color: #007acc; font-size: 14px; word-break: break-all; font-weight: bold;">${filename}</div>
    `;
    successBody.appendChild(filenameDiv);

    const pathDiv = document.createElement('div');
    pathDiv.style.cssText = 'background-color: #1e1e1e; padding: 15px; border-radius: 5px; border: 1px solid #555;';
    pathDiv.innerHTML = `
        <div style="color: #888; font-size: 12px; margin-bottom: 5px;">Download Location:</div>
        <div style="color: #ffffff; font-size: 13px; word-break: break-all;">Downloads Folder</div>
    `;
    successBody.appendChild(pathDiv);

    const successFooter = document.createElement('div');
    successFooter.className = 'modalFooter';
    successFooter.innerHTML = `
        <button class="generateBtn" onclick="document.getElementById('successModal').remove(); addMessage('File generated successfully!', false);">Done</button>
    `;

    successContent.appendChild(successHeader);
    successContent.appendChild(successBody);
    successContent.appendChild(successFooter);
    successModal.appendChild(successContent);
    document.body.appendChild(successModal);
}

function updateSelection() {
    const checkboxes = document.querySelectorAll('#payeeLookupOptions input[type="checkbox"]');
    const selectedValues = Array.from(checkboxes)
        .filter(checkbox => checkbox.checked)
        .map(checkbox => checkbox.value);

    const trigger = document.getElementById('payeeLookupTrigger');
    trigger.textContent = selectedValues.length > 0 ? selectedValues.join(', ') : 'Select Payee Lookups';

    document.getElementById('payeeLookupElementsHidden').value = selectedValues.join(',');
}

window.onclick = function(event) {
    const generateModal = document.getElementById('generateModal');
    if (event.target == generateModal) {
        GenerateFileModule.closeModal();
    }
};

// Initialize module when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    GenerateFileModule.init();
});

