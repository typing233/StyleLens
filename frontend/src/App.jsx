import React, { useState, useEffect } from 'react';
import {
  Layout,
  Menu,
  Typography,
  Button,
  Space,
  Modal,
  Select,
  message,
  Tag,
  Spin
} from 'antd';
import {
  GlobalOutlined,
  SettingOutlined,
  BarChartOutlined,
  FileTextOutlined,
  DownloadOutlined,
  EyeOutlined,
  CodeOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined
} from '@ant-design/icons';
import URLInput from './components/URLInput';
import AnalysisResult from './components/AnalysisResult';
import LLMConfig from './components/LLMConfig';
import { cssAnalyzerApi, llmConfigApi } from './services/api';
import './index.css';

const { Header, Content, Sider } = Layout;
const { Title } = Typography;

const App = () => {
  const [currentMenu, setCurrentMenu] = useState('analyze');
  const [analysisData, setAnalysisData] = useState(null);
  const [analysisId, setAnalysisId] = useState(null);
  const [llmConfigured, setLlmConfigured] = useState(false);
  const [exportModalVisible, setExportModalVisible] = useState(false);
  const [exportFormat, setExportFormat] = useState('html');
  const [exporting, setExporting] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    checkLLMStatus();
  }, []);

  const checkLLMStatus = async () => {
    try {
      const status = await llmConfigApi.getStatus();
      setLlmConfigured(status.configured);
    } catch (error) {
      console.error('Failed to check LLM status:', error);
    }
  };

  const handleAnalysisComplete = (data) => {
    if (data.analysis_id && data.result) {
      setAnalysisId(data.analysis_id);
      setAnalysisData(data.result);
    } else {
      setAnalysisData(data);
    }
    setCurrentMenu('results');
  };

  const handleLLMConfigChange = (config) => {
    setLlmConfigured(config && config.enabled);
  };

  const handleExportReport = async () => {
    setExporting(true);
    try {
      const result = await cssAnalyzerApi.exportCurrentReport(exportFormat);
      
      if (result.success) {
        message.success('Report generated successfully!');
        
        if (exportFormat === 'html' && result.report?.content) {
          const blob = new Blob([result.report.content], { type: 'text/html' });
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = result.report.filename || 'css-analysis-report.html';
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
          URL.revokeObjectURL(url);
        } else if (exportFormat === 'json') {
          const blob = new Blob([JSON.stringify(result.report, null, 2)], { type: 'application/json' });
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = 'css-analysis-report.json';
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
          URL.revokeObjectURL(url);
        }
      }
    } catch (error) {
      const errorMsg = error.response?.data?.detail || error.message || 'Unknown error';
      message.error('Failed to generate report: ' + errorMsg);
    } finally {
      setExporting(false);
      setExportModalVisible(false);
    }
  };

  const menuItems = [
    {
      key: 'analyze',
      icon: <GlobalOutlined />,
      label: 'CSS Analysis'
    },
    {
      key: 'results',
      icon: <BarChartOutlined />,
      label: 'Analysis Results',
      disabled: !analysisData
    },
    {
      key: 'llm',
      icon: <SettingOutlined />,
      label: (
        <Space>
          LLM Configuration
          {llmConfigured ? (
            <Tag icon={<CheckCircleOutlined />} color="success" style={{ margin: 0 }}>
              Connected
            </Tag>
          ) : (
            <Tag icon={<CloseCircleOutlined />} color="default" style={{ margin: 0 }}>
              Not Configured
            </Tag>
          )}
        </Space>
      )
    }
  ];

  const renderContent = () => {
    switch (currentMenu) {
      case 'analyze':
        return (
          <div>
            <URLInput onAnalysisComplete={handleAnalysisComplete} />
          </div>
        );
      
      case 'results':
        return (
          <AnalysisResult
            analysisData={analysisData}
            analysisId={analysisId}
            llmConfigured={llmConfigured}
            onExportReport={() => setExportModalVisible(true)}
          />
        );
      
      case 'llm':
        return (
          <LLMConfig onConfigChange={handleLLMConfigChange} />
        );
      
      default:
        return null;
    }
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{ 
        display: 'flex', 
        alignItems: 'center',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
      }}>
        <Space>
          <CodeOutlined style={{ fontSize: 24, color: 'white' }} />
          <Title level={3} style={{ color: 'white', margin: 0 }}>
            StyleLens
          </Title>
          <Tag color="purple">CSS Analysis Tool</Tag>
        </Space>
        
        <Space style={{ marginLeft: 'auto' }}>
          {analysisData && (
            <Button
              type="primary"
              icon={<DownloadOutlined />}
              onClick={() => setExportModalVisible(true)}
            >
              Export Report
            </Button>
          )}
        </Space>
      </Header>
      
      <Layout>
        <Sider width={240} theme="light">
          <Menu
            mode="inline"
            selectedKeys={[currentMenu]}
            onClick={({ key }) => setCurrentMenu(key)}
            style={{ height: '100%', borderRight: 0, marginTop: 16 }}
            items={menuItems}
          />
        </Sider>
        
        <Layout style={{ padding: '24px' }}>
          <Content>
            {loading ? (
              <div className="loading-container">
                <Spin size="large" />
              </div>
            ) : (
              renderContent()
            )}
          </Content>
        </Layout>
      </Layout>

      <Modal
        title={
          <Space>
            <FileTextOutlined />
            <span>Export Analysis Report</span>
          </Space>
        }
        open={exportModalVisible}
        onCancel={() => setExportModalVisible(false)}
        footer={
          <Space>
            <Button onClick={() => setExportModalVisible(false)}>
              Cancel
            </Button>
            <Button
              type="primary"
              icon={<DownloadOutlined />}
              onClick={handleExportReport}
              loading={exporting}
            >
              Export
            </Button>
          </Space>
        }
      >
        <div style={{ marginBottom: 16 }}>
          <p>Select the format for your report:</p>
        </div>
        
        <Select
          value={exportFormat}
          onChange={setExportFormat}
          style={{ width: '100%', marginBottom: 16 }}
          options={[
            { value: 'html', label: 'HTML Report (Recommended)' },
            { value: 'json', label: 'JSON Data' }
          ]}
        />
        
        <div style={{ 
          padding: 16, 
          background: '#f5f5f5', 
          borderRadius: 8,
          fontSize: 12,
          color: '#666'
        }}>
          <p><EyeOutlined /> <strong>HTML Report:</strong> Full visual report with charts, tables, and styling.</p>
          <p><FileTextOutlined /> <strong>JSON Data:</strong> Raw analysis data for programmatic use.</p>
        </div>
      </Modal>
    </Layout>
  );
};

export default App;
