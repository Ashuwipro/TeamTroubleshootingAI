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
        var aclType = firstData.type || 'Unknown';
        var options = firstData.options || 'ACH';
        var normalizedOptions = String(options).trim().replace('_', ' ');
        var now = new Date();
        var date = now.toISOString().split('T')[0].replace(/-/g, '');
        var time = now.toTimeString().split(' ')[0].replace(/:/g, '');

        // Build filename based on ESend status
        if (normalizedOptions === 'ACH & ESend') {
            return clientCompany + '_' + bankName + '_ACHXML_' + aclType + '_ESend_' + date + '_' + time + '.xml';
        } else if (normalizedOptions === 'ESend Only') {
            return clientCompany + '_' + bankName + '_ACHXML_' + aclType + '_OnlyESend_' + date + '_' + time + '.xml';
        } else {
            return clientCompany + '_' + bankName + '_ACHXML_' + aclType + '_' + date + '_' + time + '.xml';
        }
    }

    async function previewAchNachaXmlFile(context) {
        var data = context && context.data ? context.data : {};
        var fileType = context && context.fileType ? context.fileType : 'ACH NACHA XML';
        var addMessage = context && context.addMessage ? context.addMessage : function() {};
        var showGeneratePreviewModal = context && context.showGeneratePreviewModal ? context.showGeneratePreviewModal : function() {};
        var getGeneratePreviewTitle = context && context.getGeneratePreviewTitle ? context.getGeneratePreviewTitle : function() { return 'ACH NACHA XML Preview'; };
        var getAchNachaXmlPreviewSignature = context && context.getAchNachaXmlPreviewSignature ? context.getAchNachaXmlPreviewSignature : function(payload) { return JSON.stringify(payload || {}); };
        var setAchNachaXmlPreviewState = context && context.setAchNachaXmlPreviewState ? context.setAchNachaXmlPreviewState : function() {};
        var resetAchNachaXmlPreviewState = context && context.resetAchNachaXmlPreviewState ? context.resetAchNachaXmlPreviewState : function() {};

        try {
            var response = await fetch('/preview-file', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });

            if (!response.ok) {
                resetAchNachaXmlPreviewState();
                addMessage('Error: ' + await resolveResponseErrorMessage(response, 'Unable to preview file'), false);
                return;
            }

            var previewData = await response.json();
            setAchNachaXmlPreviewState({
                token: previewData.previewToken || '',
                payloadSignature: getAchNachaXmlPreviewSignature(data)
            });
            showGeneratePreviewModal(getGeneratePreviewTitle(fileType, data), previewData.content || '');
        } catch (error) {
            resetAchNachaXmlPreviewState();
            addMessage('Error: ' + error.message, false);
        }
    }

    async function generateAchNachaXmlFile(context) {
        var data = context && context.data ? context.data : {};
        var addMessage = context && context.addMessage ? context.addMessage : function() {};
        var showSuccessPopup = context && context.showSuccessPopup ? context.showSuccessPopup : function() {};
        var getAchNachaXmlPreviewState = context && context.getAchNachaXmlPreviewState ? context.getAchNachaXmlPreviewState : function() { return { token: '', payloadSignature: '' }; };
        var getAchNachaXmlPreviewSignature = context && context.getAchNachaXmlPreviewSignature ? context.getAchNachaXmlPreviewSignature : function(payload) { return JSON.stringify(payload || {}); };
        var resetAchNachaXmlPreviewState = context && context.resetAchNachaXmlPreviewState ? context.resetAchNachaXmlPreviewState : function() {};

        var previewState = getAchNachaXmlPreviewState() || {};
        var currentSignature = getAchNachaXmlPreviewSignature(data);
        if (previewState.token && previewState.payloadSignature === currentSignature) {
            data.achNachaXmlPreviewToken = previewState.token;
        } else {
            resetAchNachaXmlPreviewState();
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

    global.PcmAchNachaXmlActions = {
        previewAchNachaXmlFile: previewAchNachaXmlFile,
        generateAchNachaXmlFile: generateAchNachaXmlFile
    };
})(window);
