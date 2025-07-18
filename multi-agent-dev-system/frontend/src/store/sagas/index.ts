import { all, fork } from 'redux-saga/effects';
import projectSaga from './projectSaga';
import webSocketSaga from './webSocketSaga';

export default function* rootSaga() {
  yield all([
    fork(projectSaga),
    fork(webSocketSaga)
  ]);
}