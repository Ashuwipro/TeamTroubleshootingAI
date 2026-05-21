(function(global) {
    'use strict';

    function resolveResponseErrorMessage(response, fallbackMessage) {
        return response.json()
            .then(function(errorData) {
                return errorData && errorData.error ? errorData.error : fallbackMessage;
            })
            .catch(function() {
                return fallbackMessage;
            });
    }

    function extractDownloadFilename(response) {
        var contentDisposition = response.headers.get('Content-Disposition') || '';
        var filenameMatch = contentDisposition.match(/filename\*=UTF-8''([^;]+)|filename="?([^";]+)"?/i);
        return filenameMatch
            ? decodeURIComponent((filenameMatch[1] || filenameMatch[2] || '').trim())
            : '';
    }

    function buildFallbackFilename(context) {
        var data = context && context.data ? context.data : {};
        var formsPayload = context && Array.isArray(context.formsPayload) ? context.formsPayload : [];
        var firstData = formsPayload[0] || data;
        var clientCompany = firstData.clientCompany || 'ClientCompany';
        var bankName = firstData.bankName || 'BankName';
        var now = new Date();
        var date = now.toISOString().split('T')[0].replace(/-/g, '');
        var time = now.toTimeString().split(' ')[0].replace(/:/g, '');
        return clientCompany + '_' + bankName + '_WIRE_' + date + '_' + time + '.csv';
    }

    async function previewWireCsvFile(context) {
        var data = context && context.data ? context.data : {};
        var fileType = context && context.fileType ? context.fileType : '.CSV Wire Domestic';
        var addMessage = context && context.addMessage ? context.addMessage : function() {};
        var showGeneratePreviewModal = context && context.showGeneratePreviewModal ? context.showGeneratePreviewModal : function() {};
        var getGeneratePreviewTitle = context && context.getGeneratePreviewTitle ? context.getGeneratePreviewTitle : function() { return 'CSV Wire Domestic Preview'; };
        var getWireCsvPreviewSignature = context && context.getWireCsvPreviewSignature ? context.getWireCsvPreviewSignature : function(payload) { return JSON.stringify(payload || {}); };
        var setWireCsvPreviewState = context && context.setWireCsvPreviewState ? context.setWireCsvPreviewState : function() {};
        var resetWireCsvPreviewState = context && context.resetWireCsvPreviewState ? context.resetWireCsvPreviewState : function() {};

        try {
            var response = await fetch('/preview-file', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });

            if (!response.ok) {
                resetWireCsvPreviewState();
                addMessage('Error: ' + await resolveResponseErrorMessage(response, 'Unable to preview file'), false);
                return;
            }

            var previewData = await response.json();
            setWireCsvPreviewState({
                token: previewData.previewToken || '',
                payloadSignature: getWireCsvPreviewSignature(data)
            });
            showGeneratePreviewModal(getGeneratePreviewTitle(fileType, data), previewData.content || '');
        } catch (error) {
            resetWireCsvPreviewState();
            addMessage('Error: ' + error.message, false);
        }
    }

    async function generateWireCsvFile(context) {
        var data = context && context.data ? context.data : {};
        var addMessage = context && context.addMessage ? context.addMessage : function() {};
        var showSuccessPopup = context && context.showSuccessPopup ? context.showSuccessPopup : function() {};
        var getWireCsvPreviewState = context && context.getWireCsvPreviewState ? context.getWireCsvPreviewState : function() { return { token: '', payloadSignature: '' }; };
        var getWireCsvPreviewSignature = context && context.getWireCsvPreviewSignature ? context.getWireCsvPreviewSignature : function(payload) { return JSON.stringify(payload || {}); };
        var resetWireCsvPreviewState = context && context.resetWireCsvPreviewState ? context.resetWireCsvPreviewState : function() {};

        var previewState = getWireCsvPreviewState() || {};
        var currentSignature = getWireCsvPreviewSignature(data);
        if (previewState.token && previewState.payloadSignature === currentSignature) {
            data.wireCsvPreviewToken = previewState.token;
        } else {
            resetWireCsvPreviewState();
        }

        try {
            var response = await fetch('/generate-xml', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });

            if (!response.ok) {
                addMessage('Error: ' + await resolveResponseErrorMessage(response, 'Unable to generate file'), false);
                return;
            }

            var blob = await response.blob();
            var url = window.URL.createObjectURL(blob);
            var filename = extractDownloadFilename(response) || buildFallbackFilename(context);
            showSuccessPopup(filename, url);
        } catch (error) {
            addMessage('Error: ' + error.message, false);
        }
    }

    global.PcmWireCsvFileActions = {
        previewWireCsvFile: previewWireCsvFile,
        generateWireCsvFile: generateWireCsvFile
    };
})(window);

