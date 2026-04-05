import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';

export default function useGoogleFlow() {
  const [page, setPage] = useState('email');
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [email, setEmail] = useState('');
  const [qrImage, setQrImage] = useState(null);
  const [destination, setDestination] = useState('');
  const [error, setError] = useState('');
  // screenshots are saved locally by the server; UI doesn't need them
  const navigate = useNavigate();

  const handleError = (msg) => {
    setError(msg || 'An unexpected error occurred');
  };

  const submitEmail = async (emailAddr) => {
    setLoading(true);
    setError('');
    try {
      // FastAPI endpoint expects form-encoded data rather than JSON
      const form = new FormData();
      form.append('email', emailAddr);
      const resp = await api.post('/google/login', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      const data = resp.data;
      if (data.success) {
        setEmail(emailAddr);
        setSessionId(data.session_id);
        switch (data.page) {
          case 'password':
            setPage('password');
            break;
          case 'success':
            navigate('/');
            break;
          default:
            handleError(`Unexpected page type: ${data.page}`);
        }
      } else {
        handleError(data.error);
      }
    } catch (e) {
      handleError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const submitPassword = async (password) => {
    setLoading(true);
    setError('');
    try {
      const form = new FormData();
      form.append('session_id', sessionId);
      form.append('password', password);
      const resp = await api.post('/google/password', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      const data = resp.data;
      if (data.success) {
        switch (data.page) {
          case '2fa':
            setDestination(data.destination || '');
            setPage('2fa');
            break;
          case 'qr':
            setQrImage(data.qr_image);
            setPage('qr');
            break;
          case 'success':
            navigate('/google-success');
            break;
          default:
            handleError(`Unexpected page type: ${data.page}`);
        }
      } else {
        handleError(data.error);
      }
    } catch (e) {
      handleError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const submit2fa = async (code) => {
    setLoading(true);
    setError('');
    try {
      const form = new FormData();
      form.append('session_id', sessionId);
      form.append('code', code);
      const resp = await api.post('/google/2fa', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      const data = resp.data;
      if (data.success) {
        if (data.page === 'success') {
          navigate('/google-success');
        } else {
          handleError(`Unexpected page after 2FA: ${data.page}`);
        }
      } else {
        handleError(data.error);
      }
    } catch (e) {
      handleError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const continueAfterQr = () => {
    // for now we just restart flow or treat as success
    setPage('email');
    setEmail('');
    setQrImage(null);
    setSessionId(null);
  };

  return {
    page,
    loading,
    email,
    qrImage,
    error,
    submitEmail,
    submitPassword,
    submit2fa,
    continueAfterQr,
    destination,
  };
}
