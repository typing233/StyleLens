import React, { useState } from 'react';
import {
  Card,
  Form,
  Input,
  Button,
  Checkbox,
  message,
  Space,
  Alert,
  Typography
} from 'antd';
import {
  SearchOutlined,
  GlobalOutlined,
  CodeOutlined,
  LinkOutlined
} from '@ant-design/icons';
import { cssAnalyzerApi } from '../services/api';

const { Text, Title } = Typography;

const URLInput = ({ onAnalysisComplete }) => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [lastAnalyzedUrl, setLastAnalyzedUrl] = useState(null);

  const handleAnalyze = async (values) => {
    setLoading(true);
    try {
      const result = await cssAnalyzerApi.analyzeUrl(values.url, {
        include_inline: values.include_inline,
        include_external: values.include_external,
        deep_analysis: values.deep_analysis
      });
      
      setLastAnalyzedUrl(values.url);
      message.success('Analysis completed successfully!');
      
      if (onAnalysisComplete) {
        onAnalysisComplete(result);
      }
    } catch (error) {
      const errorMsg = error.response?.data?.detail || error.message || 'Unknown error';
      message.error('Analysis failed: ' + errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const sampleUrls = [
    'https://example.com',
    'https://www.wikipedia.org',
    'https://www.google.com'
  ];

  return (
    <Card
      title={
        <Space>
          <GlobalOutlined style={{ fontSize: 20 }} />
          <span>CSS Analysis</span>
        </Space>
      }
      style={{ marginBottom: 24 }}
    >
      <Alert
        message="How it works"
        description={
          <div>
            <p>Enter a webpage URL to analyze its CSS architecture. The system will:</p>
            <ul>
              <li>Extract all inline and external CSS styles</li>
              <li>Parse CSS into Abstract Syntax Tree (AST)</li>
              <li>Build class relationship graphs</li>
              <li>Detect redundant styles and optimization opportunities</li>
              <li>Generate comprehensive analysis reports</li>
            </ul>
          </div>
        }
        type="info"
        showIcon
        style={{ marginBottom: 24 }}
      />

      <Form
        form={form}
        layout="vertical"
        onFinish={handleAnalyze}
        initialValues={{
          url: '',
          include_inline: true,
          include_external: true,
          deep_analysis: true
        }}
      >
        <Form.Item
          name="url"
          label={
            <Space>
              <LinkOutlined />
              <span>Target URL</span>
            </Space>
          }
          rules={[
            { required: true, message: 'Please enter a URL' },
            { type: 'url', message: 'Please enter a valid URL' }
          ]}
          extra="Enter the full URL of the webpage you want to analyze (including http:// or https://)"
        >
          <Input
            prefix={<GlobalOutlined />}
            placeholder="https://example.com"
            size="large"
            suffix={
              <Button
                type="primary"
                icon={<SearchOutlined />}
                onClick={() => form.submit()}
                loading={loading}
                size="large"
              >
                Analyze
              </Button>
            }
          />
        </Form.Item>

        <Form.Item label="Analysis Options">
          <Space wrap>
            <Form.Item name="include_inline" valuePropName="checked" noStyle>
              <Checkbox>Include inline styles</Checkbox>
            </Form.Item>
            <Form.Item name="include_external" valuePropName="checked" noStyle>
              <Checkbox>Include external CSS</Checkbox>
            </Form.Item>
            <Form.Item name="deep_analysis" valuePropName="checked" noStyle>
              <Checkbox>Deep analysis (relationship mapping)</Checkbox>
            </Form.Item>
          </Space>
        </Form.Item>

        <Form.Item>
          <Text type="secondary">
            <Space>
              <CodeOutlined />
              <span>Quick test with sample URLs:</span>
            </Space>
          </Text>
          <div style={{ marginTop: 8 }}>
            <Space wrap>
              {sampleUrls.map((url, index) => (
                <Button
                  key={index}
                  type="link"
                  onClick={() => form.setFieldValue('url', url)}
                  style={{ padding: '4px 8px' }}
                >
                  {url}
                </Button>
              ))}
            </Space>
          </div>
        </Form.Item>
      </Form>

      {lastAnalyzedUrl && (
        <Alert
          message={`Last analyzed: ${lastAnalyzedUrl}`}
          type="success"
          showIcon
          style={{ marginTop: 16 }}
        />
      )}
    </Card>
  );
};

export default URLInput;
