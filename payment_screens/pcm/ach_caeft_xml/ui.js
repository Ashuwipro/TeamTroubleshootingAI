(function(global) {
    'use strict';

    function createSelectGroup(targetColumn, labelText, fieldName, options, isRequired, requiredAsteriskMarkup, selectId) {
        var group = document.createElement('div');
        group.className = 'formGroup';

        var label = document.createElement('label');
        label.className = 'formLabel';
        if (isRequired) {
            label.innerHTML = '<span style="white-space: nowrap;">' + labelText + ':' + requiredAsteriskMarkup + '</span>';
        } else {
            label.textContent = labelText + ':';
        }

        var select = document.createElement('select');
        select.className = 'formInput';
        select.name = fieldName;
        if (selectId) {
            select.id = selectId;
        }

        options.forEach(function(optionDef) {
            var option = document.createElement('option');
            option.value = optionDef.value;
            option.textContent = optionDef.label;
            select.appendChild(option);
        });

        group.appendChild(label);
        group.appendChild(select);
        targetColumn.appendChild(group);
        return select;
    }

    function toggleEsendSection(optionsSelect, esendSection) {
        if (!optionsSelect || !esendSection) {
            return;
        }
        var selected = String(optionsSelect.value || '').trim();
        esendSection.style.display = (selected === 'ACH & ESend' || selected === 'ESend_Only') ? 'block' : 'none';
    }

    function renderAchCaeftXmlForm(context) {
        if (!context || !context.modalBody || typeof context.createTagGroup !== 'function') {
            return false;
        }

        var modalBody = context.modalBody;
        var createTagGroup = context.createTagGroup;
        var updateGenerateButtonState = context.updateGenerateButtonState || function() {};
        var requiredAsteriskMarkup = context.requiredAsteriskMarkup || '<span style="color: #ff5555; margin-left: 2px; display: inline-block;">*</span>';

        var leftColumn = document.createElement('div');
        leftColumn.className = 'formColumn';
        leftColumn.style.borderRight = '1px solid #555';
        leftColumn.style.paddingRight = '15px';

        var middleColumn = document.createElement('div');
        middleColumn.className = 'formColumn';
        middleColumn.style.borderRight = '1px solid #555';
        middleColumn.style.paddingRight = '15px';

        var rightColumn = document.createElement('div');
        rightColumn.className = 'formColumn';

        createTagGroup(leftColumn, 'Batches Quantity', 'batchesQuantity', 'Enter quantity (e.g. 3)', false, { numericPositiveOnly: true, singleValueOnly: true });
        createTagGroup(leftColumn, 'Transactions Count', 'transactionsCount', 'Enter positive counts...', true, { numericPositiveOnly: true });
        createTagGroup(leftColumn, 'ACH Comp IDs', 'achCompIds', 'Enter ACH Comp IDs...', true);
        createTagGroup(leftColumn, 'ACH Comp Names', 'achCompNames', 'Enter ACH Comp Names...', true);
        createTagGroup(leftColumn, 'ABAs', 'abas', 'Enter ABA numbers...', true, { numericOnly: true, exactLength: 9 });

        createTagGroup(middleColumn, 'Payee IDs', 'payeeIds', 'Enter Payee IDs...', true);
        createSelectGroup(middleColumn, 'Payee Lookup Type', 'payeeLookupType', [
            { value: 'No Flag', label: 'No Flag' },
            { value: 'DB', label: 'DB' },
            { value: 'FILE', label: 'FILE' },
            { value: 'NONE', label: 'NONE' }
        ], false, requiredAsteriskMarkup);
        createTagGroup(middleColumn, 'Payee Lookup Elements', 'payeeLookupElements', 'Enter lookup elements...', true);

        createTagGroup(middleColumn, 'Funding Account Number', 'fundingAccountNumber', 'Enter Funding Account Number...', true);
        createTagGroup(middleColumn, 'Return Account Number', 'returnAccountNumber', 'Enter Return Account Number...', true);
        createTagGroup(middleColumn, 'Account Number', 'accountNumber', 'Enter Account Number...', true);

        createTagGroup(rightColumn, 'Client Company', 'clientCompany', 'Enter Client Company...', false, { singleValueOnly: true }, true);
        createTagGroup(rightColumn, 'Bank Name', 'bankName', 'Enter Bank Name...', false, { singleValueOnly: true }, true);

        createSelectGroup(rightColumn, 'Batch Credit/Debit', 'batchCreditDebit', [
            { value: 'Credit', label: 'Credit' },
            { value: 'Debit', label: 'Debit' }
        ], true, requiredAsteriskMarkup);

        createSelectGroup(rightColumn, 'Transaction Credit/Debit', 'transactionCreditDebit', [
            { value: 'Credit', label: 'Credit' },
            { value: 'Debit', label: 'Debit' }
        ], true, requiredAsteriskMarkup);

        var optionsSelect = createSelectGroup(rightColumn, 'Options', 'options', [
            { value: 'ACH', label: 'ACH' },
            { value: 'ACH & ESend', label: 'ACH & ESend' },
            { value: 'ESend_Only', label: 'ESend_Only' }
        ], true, requiredAsteriskMarkup, 'optionsSelect');

        var esendSection = document.createElement('div');
        esendSection.id = 'esendDetails';
        esendSection.style.display = 'none';
        createSelectGroup(esendSection, 'ESend App Type', 'esendAppType', [
            { value: 'Name', label: 'Name' },
            { value: 'ID', label: 'ID' }
        ], true, requiredAsteriskMarkup);
        createTagGroup(esendSection, 'ESend App Value', 'esendAppValue', 'Enter ESend App values...', true, {}, true);
        createTagGroup(esendSection, 'ESend Profile Keys', 'esendProfileKeys', 'Enter ESend Profile Keys...', true, {}, true);
        createTagGroup(esendSection, 'Payee Emails', 'payeeEmails', 'Enter Payee Emails...', true, {}, true);
        rightColumn.appendChild(esendSection);

        optionsSelect.addEventListener('change', function() {
            toggleEsendSection(optionsSelect, esendSection);
            updateGenerateButtonState();
        });
        toggleEsendSection(optionsSelect, esendSection);

        modalBody.appendChild(leftColumn);
        modalBody.appendChild(middleColumn);
        modalBody.appendChild(rightColumn);

        updateGenerateButtonState();
        return true;
    }

    global.PcmAchCaeftXmlUI = {
        renderAchCaeftXmlForm: renderAchCaeftXmlForm
    };
})(window);

